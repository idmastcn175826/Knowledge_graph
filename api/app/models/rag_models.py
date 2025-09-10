from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils import Base


class RAGCollection(Base):
    """RAG文档集合模型"""
    __tablename__ = "rag_collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    # 添加服务器默认值和索引，便于按创建时间查询
    created_at = Column(DateTime, default=datetime.utcnow, server_default=datetime.utcnow().isoformat(), index=True)

    # 关系
    documents = relationship("RAGDocument", back_populates="collection", cascade="all, delete-orphan")

    # 虚拟字段（用于响应）
    @property
    def document_count(self):
        """动态计算文档数量"""
        return len(self.documents) if self.documents else 0


class RAGDocument(Base):
    """RAG文档模型"""
    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("rag_collections.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    # 扩大文件类型字段长度，支持更多类型
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # 用BigInteger支持大文件
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="uploaded", index=True)  # 添加索引，便于按状态筛选
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True, index=True)

    # 关系
    collection = relationship("RAGCollection", back_populates="documents")
    chunks = relationship("RAGChunk", back_populates="document", cascade="all, delete-orphan")


class RAGChunk(Base):
    """RAG文档片段模型"""
    __tablename__ = "rag_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("rag_documents.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Text, nullable=False)  # 存储向量的JSON字符串
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    document = relationship("RAGDocument", back_populates="chunks")
