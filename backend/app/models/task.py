from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.db import Base


class Task(Base):
    """任务表模型"""
    __tablename__ = "tasks"  # 数据库表名

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False)  # 唯一任务标识
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 关联用户
    task_type = Column(String(50), nullable=False)  # 任务类型: kg_create, file_parse等
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 进度(0-100)
    kg_id = Column(String(64), nullable=True, index=True)  # 关联知识图谱ID
    file_ids = Column(Text, nullable=True)  # 关联文件ID，用逗号分隔
    result = Column(Text, nullable=True)  # 任务结果
    error_msg = Column(Text, nullable=True)  # 错误信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)  # 开始时间
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 完成时间

    # 关联用户
    user = relationship("User", backref="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, task_id='{self.task_id}', status='{self.status}')>"
