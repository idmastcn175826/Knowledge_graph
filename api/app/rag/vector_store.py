import logging
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from app.config.config import settings

# 配置国内模型下载源（解决下载慢问题）
os.environ["CHROMA_MODEL_DOWNLOAD_HOST"] = "https://cdn-lfs.huggingface.co"

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self):
        # 修复：移除不被支持的chroma_client_timeout参数
        self.client = chromadb.PersistentClient(
            path=settings.vector_store_path,  # 数据持久化路径
            settings=Settings(
                anonymized_telemetry=False,  # 关闭匿名统计
                is_persistent=True
                # 移除不支持的超时参数
            )
        )

    def create_collection(self, collection_id: int):
        """创建向量集合"""
        collection_name = f"rag_collection_{collection_id}"
        try:
            # 优化：使用列表检查而非异常捕获
            collections = self.client.list_collections()
            if any(col.name == collection_name for col in collections):
                logger.warning(f"向量集合 {collection_name} 已存在")
                return

            self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
            )
            logger.info(f"创建向量集合: {collection_name}")
        except Exception as e:
            logger.error(f"创建向量集合失败: {str(e)}")
            raise

    def delete_collection(self, collection_id: int):
        """删除向量集合"""
        collection_name = f"rag_collection_{collection_id}"
        try:
            # 检查集合是否存在
            try:
                self.client.get_collection(name=collection_name)
            except ValueError:
                logger.warning(f"向量集合 {collection_name} 不存在，无需删除")
                return

            self.client.delete_collection(name=collection_name)
            logger.info(f"删除向量集合: {collection_name}")
        except Exception as e:
            logger.error(f"删除向量集合失败: {str(e)}")

    def get_collection(self, collection_id: int):
        """获取向量集合"""
        collection_name = f"rag_collection_{collection_id}"
        try:
            return self.client.get_collection(name=collection_name)
        except Exception as e:
            logger.error(f"获取向量集合 {collection_id} 失败: {str(e)}")
            raise

    def add_documents(self, collection_id: int, documents: List[Dict], embeddings: List[List[float]], document_id: int):
        """添加文档到向量集合"""
        try:
            collection = self.get_collection(collection_id)

            # 准备数据
            ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(documents))]
            texts = [doc["text"] for doc in documents]
            metadatas = [
                {
                    "document_id": document_id,
                    "chunk_index": i,
                    "start_index": doc.get("start_index", 0),
                    "end_index": doc.get("end_index", 0)
                } for i, doc in enumerate(documents)
            ]

            # 添加到集合
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"成功添加 {len(documents)} 个文档片段到集合 {collection_id}")
        except Exception as e:
            logger.error(f"添加文档到向量集合失败: {str(e)}")
            raise

    def remove_document(self, collection_id: int, document_id: int):
        """从向量集合中移除文档"""
        try:
            collection = self.get_collection(collection_id)

            # 获取所有属于该文档的片段ID
            results = collection.get(where={"document_id": document_id})
            if results and results["ids"]:
                collection.delete(ids=results["ids"])
                logger.info(f"从集合 {collection_id} 中移除文档 {document_id} 的 {len(results['ids'])} 个片段")
        except Exception as e:
            logger.error(f"从向量集合中移除文档失败: {str(e)}")
            raise

    def semantic_search(self, collection_id: int, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """语义搜索"""
        try:
            collection = self.get_collection(collection_id)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            return self._format_results(results)
        except Exception as e:
            logger.error(f"语义搜索失败: {str(e)}")
            # 检查是否是集合不存在的错误
            if "does not exist" in str(e).lower() or "不存在" in str(e):
                raise  # 让上层处理集合不存在的情况
            return []

    def keyword_search(self, collection_id: int, query: str, top_k: int = 5) -> List[Dict]:
        """关键词搜索"""
        try:
            collection = self.get_collection(collection_id)
            # 修复：移除不支持的timeout参数
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )

            return self._format_results(results)
        except Exception as e:
            logger.error(f"关键词搜索失败: {str(e)}")
            return []

    def hybrid_search(self, collection_id: int, query: str, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """混合搜索（结合语义和关键词）"""
        try:
            collection = self.get_collection(collection_id)

            # 执行语义搜索
            semantic_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2  # 获取更多结果用于融合
            )

            # 执行关键词搜索
            keyword_results = collection.query(
                query_texts=[query],
                n_results=top_k * 2  # 获取更多结果用于融合
            )

            # 结果融合
            combined_results = self._fuse_results(semantic_results, keyword_results, top_k)

            return combined_results
        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}")
            # 降级处理：使用语义搜索结果
            return self.semantic_search(collection_id, query_embedding, top_k)

    def _format_results(self, results) -> List[Dict]:
        """格式化搜索结果"""
        formatted = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted.append({
                    "text": results["documents"][0][i],
                    "score": results["distances"][0][i] if results["distances"] else 0,
                    "document_id": results["metadatas"][0][i]["document_id"] if results["metadatas"] else 0,
                    "chunk_index": results["metadatas"][0][i]["chunk_index"] if results["metadatas"] else 0
                })
        return formatted

    def _fuse_results(self, semantic_results, keyword_results, top_k: int) -> List[Dict]:
        """融合语义和关键词搜索结果"""
        semantic_formatted = self._format_results(semantic_results)
        keyword_formatted = self._format_results(keyword_results)

        # 去除重复
        seen_ids = set()
        combined = []

        # 先添加语义结果
        for result in semantic_formatted:
            result_id = f"{result['document_id']}_{result['chunk_index']}"
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                combined.append(result)
            if len(combined) >= top_k:
                break

        # 补充关键词结果
        if len(combined) < top_k:
            for result in keyword_formatted:
                result_id = f"{result['document_id']}_{result['chunk_index']}"
                if result_id not in seen_ids:
                    seen_ids.add(result_id)
                    combined.append(result)
                if len(combined) >= top_k:
                    break

        return combined
