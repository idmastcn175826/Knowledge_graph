from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.db import Base


class File(Base):
    """
    文件表模型，存储用户上传的文件元数据

    与User是多对一关系（一个用户可上传多个文件）
    记录文件的基本信息、处理状态及关联的知识图谱
    """
    __tablename__ = "files"  # 数据库表名

    id = Column(Integer,primary_key=True,index=True,comment="自增主键ID")
    file_id = Column(String(64),unique=True,index=True,nullable=False,comment="唯一文件标识（UUID）")
    filename = Column(String(255),nullable=False,comment="原始文件名（包含扩展名）")
    file_path = Column(String(512),nullable=False,comment="文件在服务器中的存储路径")
    file_size = Column(Integer,nullable=False,comment="文件大小（字节）")
    file_type = Column(String(50),nullable=False,comment="文件类型（如txt/pdf/docx等）")
    mime_type = Column(String(100),nullable=True,comment="MIME类型（如text/plain/application/pdf）")
    user_id = Column(Integer,ForeignKey("users.id"),nullable=False,index=True,comment="关联的用户ID")
    status = Column(String(20),default="uploaded",index=True,comment="文件状态：uploaded(已上传)/processing(处理中)/processed(已处理)/failed(处理失败)")
    is_processed = Column(Boolean,default=False,comment="是否已被处理（如用于构建知识图谱）")
    kg_ids = Column(Text,nullable=True,comment="关联的知识图谱ID列表，用逗号分隔")
    processed_time = Column(DateTime(timezone=True),nullable=True,comment="文件处理完成时间")
    created_at = Column(DateTime(timezone=True),server_default=func.now(),comment="文件上传时间")
    updated_at = Column(DateTime(timezone=True),onupdate=func.now(),comment="记录更新时间")

    # 创建复合索引，优化常见查询场景
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )

    # 关联关系
    user = relationship("User",back_populates="files")

    def __repr__(self):
        return f"<File(file_id='{self.file_id}', filename='{self.filename}', status='{self.status}')>"
