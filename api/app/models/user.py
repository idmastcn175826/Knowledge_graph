
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.db import Base  


class User(Base):
    """用户表模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="自增主键ID")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名（登录用）")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="用户邮箱")
    password_hash = Column(String(255), nullable=False, comment="加密后的密码")
    full_name = Column(String(100), nullable=True, comment="用户全名")
    role = Column(String(20), default="user", comment="用户角色")
    is_active = Column(Boolean, default=True, comment="账号是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 修复：用字符串引用模型名，替代直接导入 HealthData/EmergencyEvent
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")  # 假设 File 模型存在
    knowledge_graphs = relationship("KnowledgeGraph", back_populates="user", cascade="all, delete-orphan")  # 假设该模型存在
    health_data = relationship("HealthData", back_populates="user", cascade="all, delete-orphan")  # 字符串引用
    emergency_events = relationship("EmergencyEvent", back_populates="user", cascade="all, delete-orphan")  # 补充级联删除
    emergency_contacts = relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")  # 补充级联删除

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"