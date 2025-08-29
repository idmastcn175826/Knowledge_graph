from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.db import Base


class File(Base):
    """文件表模型"""
    __tablename__ = "files"  # 数据库表名

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(64), unique=True, index=True, nullable=False)  # 唯一文件标识
    filename = Column(String(255), nullable=False)  # 文件名
    file_path = Column(String(512), nullable=False)  # 文件存储路径
    file_size = Column(Float, nullable=False)  # 文件大小(字节)
    file_type = Column(String(50), nullable=False)  # 文件类型
    mime_type = Column(String(100), nullable=True)  # MIME类型
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 关联用户
    is_processed = Column(Boolean, default=False)  # 是否已处理
    processed_time = Column(DateTime(timezone=True), nullable=True)  # 处理时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联用户
    user = relationship("User", backref="files")

    def __repr__(self):
        return f"<File(id={self.id}, filename='{self.filename}')>"
