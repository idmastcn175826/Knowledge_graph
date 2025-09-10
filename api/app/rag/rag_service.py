import logging
from typing import List, Dict, Any, Optional
import requests
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.config.config import settings
from app.models.rag_models import RAGCollection, RAGDocument
from app.rag.embedding.embedding_service import EmbeddingService
from app.rag.file_processor import FileProcessor
from app.rag.vector_store import VectorStoreService
from app.utils.exceptions import RAGException

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStoreService()
        self.embedding_service = EmbeddingService()
        self.file_processor = FileProcessor()

    def create_collection(self, name: str, description: Optional[str] = None) -> RAGCollection:
        """创建新的RAG集合"""
        try:
            # 检查集合是否已存在
            existing = self.db.query(RAGCollection).filter(RAGCollection.name == name).first()
            if existing:
                raise RAGException(f"集合名称 '{name}' 已存在")

            # 创建数据库记录
            collection = RAGCollection(name=name, description=description)
            self.db.add(collection)
            self.db.commit()  # 提交事务，获取自增ID
            self.db.refresh(collection)

            # 在向量数据库中创建集合
            try:
                self.vector_store.create_collection(collection.id)
            except Exception as e:
                # 关键修复：如果向量集合创建失败，回滚数据库记录
                self.db.delete(collection)
                self.db.commit()
                logger.error(f"向量集合创建失败，回滚数据库记录: {str(e)}")
                raise RAGException(f"创建集合失败: 向量存储错误 - {str(e)}")

            return collection
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"数据库错误: {str(e)}")
            raise RAGException("创建集合时发生数据库错误")
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建集合失败: {str(e)}")
            raise RAGException("创建集合失败")

    def get_collection(self, collection_id: int) -> Optional[RAGCollection]:
        """获取集合信息"""
        try:
            return self.db.query(RAGCollection).filter(RAGCollection.id == collection_id).first()
        except SQLAlchemyError as e:
            logger.error(f"数据库错误: {str(e)}")
            raise RAGException("获取集合信息失败")

    def list_collections(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有集合列表，返回包含文档计数的字典列表"""
        try:
            # 关键修复：使用JOIN和COUNT在数据库层面计算文档数量
            # 避免后续对集合对象的document_count属性赋值
            query = self.db.query(
                RAGCollection,
                func.count(RAGDocument.id).label('document_count')
            ).outerjoin(
                RAGDocument,
                (RAGCollection.id == RAGDocument.collection_id) &
                (RAGDocument.status == "processed")
            ).group_by(
                RAGCollection.id
            ).offset(skip).limit(limit)

            # 执行查询并转换结果为字典列表
            results = []
            for collection, doc_count in query.all():
                results.append({
                    "id": collection.id,
                    "name": collection.name,
                    "description": collection.description,
                    "created_at": collection.created_at,
                    "document_count": doc_count  # 使用查询计算的文档数量
                })

            return results
        except SQLAlchemyError as e:
            logger.error(f"数据库错误: {str(e)}")
            raise RAGException("获取集合列表失败")

    def delete_collection(self, collection_id: int) -> bool:
        """删除集合"""
        try:
            collection = self.db.query(RAGCollection).filter(RAGCollection.id == collection_id).first()
            if not collection:
                return False

            # 删除向量数据库中的集合
            self.vector_store.delete_collection(collection_id)

            # 删除数据库记录
            self.db.delete(collection)
            self.db.commit()

            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"数据库错误: {str(e)}")
            raise RAGException("删除集合时发生数据库错误")
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除集合失败: {str(e)}")
            raise RAGException("删除集合失败")

    def create_document(
            self,
            collection_id: int,
            filename: str,
            file_path: str,
            file_type: str,
            file_size: int
    ) -> RAGDocument:
        """创建文档记录"""
        try:
            # 检查集合是否存在
            collection = self.get_collection(collection_id)
            if not collection:
                raise RAGException(f"集合 ID {collection_id} 不存在")

            # 创建文档记录
            document = RAGDocument(
                collection_id=collection_id,
                filename=filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                status="uploaded"
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            return document
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"数据库错误: {str(e)}")
            raise RAGException("创建文档记录时发生数据库错误")
        except RAGException as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建文档记录失败: {str(e)}")
            raise RAGException("创建文档记录失败")

    def process_and_index_document(self, document_id: int, file_path: str):
        """处理和索引文档（在后台任务中调用）"""
        try:
            # 获取文档记录
            document = self.db.query(RAGDocument).filter(RAGDocument.id == document_id).first()
            if not document:
                logger.error(f"文档 ID {document_id} 不存在")
                return

            # 更新状态为处理中
            document.status = "processing"
            self.db.commit()

            try:
                # 处理文档
                chunks = self.file_processor.process_file(file_path, document.file_type)

                if not chunks:
                    raise RAGException("文档处理失败，未提取到内容")

                # 生成嵌入向量
                embeddings = self.embedding_service.generate_embeddings([chunk["text"] for chunk in chunks])

                # 索引到向量数据库
                self.vector_store.add_documents(
                    collection_id=document.collection_id,
                    documents=chunks,
                    embeddings=embeddings,
                    document_id=document_id
                )

                # 更新状态为已完成
                document.status = "processed"
                document.chunk_count = len(chunks)
                self.db.commit()

                logger.info(f"文档 {document.filename} 处理完成，共 {len(chunks)} 个片段")

            except Exception as e:
                # 更新状态为失败
                document.status = "failed"
                document.error_message = str(e)
                self.db.commit()
                logger.error(f"文档处理失败: {str(e)}")

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"数据库错误: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"处理文档时发生未知错误: {str(e)}")

    def remove_document(self, collection_id: int, document_id: int) -> bool:
        """从集合中移除文档"""
        try:
            document = self.db.query(RAGDocument).filter(
                RAGDocument.id == document_id,
                RAGDocument.collection_id == collection_id
            ).first()

            if not document:
                return False

            # 从向量数据库中移除文档
            self.vector_store.remove_document(collection_id, document_id)

            # 删除数据库记录
            self.db.delete(document)
            self.db.commit()

            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"数据库错误: {str(e)}")
            raise RAGException("移除文档时发生数据库错误")
        except Exception as e:
            self.db.rollback()
            logger.error(f"移除文档失败: {str(e)}")
            raise RAGException("移除文档失败")

    def list_documents(self, collection_id: int, skip: int = 0, limit: int = 100) -> List[RAGDocument]:
        """获取集合中的所有文档"""
        try:
            documents = self.db.query(RAGDocument).filter(
                RAGDocument.collection_id == collection_id
            ).offset(skip).limit(limit).all()

            return documents
        except SQLAlchemyError as e:
            logger.error(f"数据库错误: {str(e)}")
            raise RAGException("获取文档列表失败")

    def query(
            self,
            collection_id: int,
            query: str,
            top_k: int = 5,
            mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """查询RAG系统"""
        try:
            # 验证集合是否存在
            collection = self.get_collection(collection_id)
            if not collection:
                raise RAGException(f"集合 ID {collection_id} 不存在")

            # 验证向量集合是否存在
            try:
                self.vector_store.get_collection(collection_id)
            except Exception as e:
                raise RAGException(f"集合向量存储不存在: {str(e)}")

            # 生成查询嵌入
            query_embedding = self.embedding_service.generate_embeddings([query])[0]

            # 从向量数据库中检索相关文档
            if mode == "semantic":
                results = self.vector_store.semantic_search(
                    collection_id=collection_id,
                    query_embedding=query_embedding,
                    top_k=top_k
                )
            elif mode == "keyword":
                results = self.vector_store.keyword_search(
                    collection_id=collection_id,
                    query=query,
                    top_k=top_k
                )
            else:  # hybrid
                results = self.vector_store.hybrid_search(
                    collection_id=collection_id,
                    query=query,
                    query_embedding=query_embedding,
                    top_k=top_k
                )

            if not results:
                return {
                    "answer": "抱歉，我没有找到相关的信息来回答您的问题。",
                    "sources": [],
                    "confidence": 0.0
                }

            # 使用LLM生成答案
            answer, confidence = self._generate_answer(query, results)

            # 准备来源信息
            sources = []
            for result in results:
                # 获取文档信息
                document = self.db.query(RAGDocument).filter(RAGDocument.id == result["document_id"]).first()
                if document:
                    sources.append({
                        "document_id": document.id,
                        "filename": document.filename,
                        "content": result["text"],
                        "score": result["score"]
                    })

            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            raise RAGException("查询失败")

    def _generate_answer(self, query: str, context_results: List[Dict]) -> tuple:
        """使用LLM生成答案（完整实现）"""
        # 构建上下文
        context = "\n\n".join([f"来源 {i + 1}: {result['text']}" for i, result in enumerate(context_results)])

        # 构建提示
        prompt = f"""基于以下上下文信息，请回答用户的问题。
        上下文信息:
        {context}
        用户问题: {query}
        请提供准确、简洁的回答，并引用相关的上下文信息。如果上下文信息不足以回答问题，请如实告知。"""

        try:
            # Qwen API信息
            if not settings.QWEN_API_BASE_URL or not settings.QWEN_DEFAULT_API_KEY:
                raise RAGException("Qwen模型配置不完整，请检查API地址和密钥")

            # 调用Qwen API key
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.QWEN_DEFAULT_API_KEY}"
            }

            payload = {
                "model": settings.QWEN_MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1024
            }

            response = requests.post(
                settings.QWEN_API_BASE_URL,
                headers=headers,
                json=payload,
                timeout=settings.LLM_TIMEOUT  # 使用配置中的超时设置
            )

            response.raise_for_status()  # 抛出HTTP错误
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            confidence = 0.85  #温度

            return answer, confidence

        except Exception as e:
            logger.error(f"LLM服务调用失败: {str(e)}")
            # 降级处理：返回基于上下文的简单回答
            return f"无法生成回答: {str(e)}。相关信息: {context[:200]}...", 0.0