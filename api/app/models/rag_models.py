from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime


class RAGCollection(Base):
    """RAG文档集合模型"""
    __tablename__ = "rag_collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    documents = relationship("RAGDocument", back_populates="collection", cascade="all, delete-orphan")

    # 虚拟字段（用于响应）
    document_count = 0


class RAGDocument(Base):
    """RAG文档模型"""
    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("rag_collections.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="uploaded")  # uploaded, processing, processed, failed
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # 关系
    collection = relationship("RAGCollection", back_populates="documents")