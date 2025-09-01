from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.utils.db import Base


class KnowledgeGraph(Base):
    __tablename__ = "knowledge_graphs"

    id = Column(Integer, primary_key=True, index=True)
    kg_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    entity_count = Column(Integer, default=0)
    relation_count = Column(Integer, default=0)
    file_ids = Column(Text, comment="构建该知识图谱所用的文件ID列表，用逗号分隔")
    progress = Column(Integer, default=0)
    build_message = Column(Text, comment="构建消息")

    # 关联User模型
    user = relationship(
        "User",
        back_populates="knowledge_graphs"
    )
