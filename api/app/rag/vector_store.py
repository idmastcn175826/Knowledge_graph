import logging
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from app.config.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=settings.vector_store_path
        ))

    def create_collection(self, collection_id: int):
        """创建向量集合"""
        collection_name = f"rag_collection_{collection_id}"
        try:
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
            logger.error(f"获取向量集合失败: {str(e)}")
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
            return []

    def keyword_search(self, collection_id: int, query: str, top_k: int = 5) -> List[Dict]:
        """关键词搜索"""
        try:
            collection = self.get_collection(collection_id)
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

            # 结果融合（简化实现：优先选择语义搜索结果）
            # 在实际应用中，可以使用更复杂的融合算法如RRF (Reciprocal Rank Fusion)
            combined_results = self._fuse_results(semantic_results, keyword_results, top_k)

            return combined_results
        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}")
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
        # 简化实现：优先选择语义搜索结果，补充关键词搜索结果
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

        # 如果不够，补充关键词结果
        if len(combined) < top_k:
            for result in keyword_formatted:
                result_id = f"{result['document_id']}_{result['chunk_index']}"
                if result_id not in seen_ids:
                    seen_ids.add(result_id)
                    combined.append(result)
                if len(combined) >= top_k:
                    break

        return combined