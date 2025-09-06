from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.utils.db import Base


class HealthData(Base):
    __tablename__ = "health_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_id = Column(String(100))  # 设备标识
    device_type = Column(String(50))  # 设备类型

    # 健康指标
    heart_rate = Column(Integer)  # 心率
    blood_oxygen = Column(Float)  # 血氧饱和度
    systolic_bp = Column(Integer)  # 收缩压
    diastolic_bp = Column(Integer)  # 舒张压
    blood_glucose = Column(Float)  # 血糖
    temperature = Column(Float)  # 体温
    respiratory_rate = Column(Integer)  # 呼吸频率

    # 活动数据
    steps = Column(Integer)  # 步数
    calories = Column(Float)  # 卡路里
    distance = Column(Float)  # 距离

    # 位置和环境数据
    latitude = Column(Float)  # 纬度
    longitude = Column(Float)  # 经度
    altitude = Column(Float)  # 海拔
    environment_temp = Column(Float)  # 环境温度
    environment_humidity = Column(Float)  # 环境湿度

    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系 - 使用relationship而不是Column
    user = relationship("User", back_populates="health_data")
    emergency_events = relationship("EmergencyEvent", back_populates="health_data")


class EmergencyEvent(Base):
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    health_data_id = Column(Integer, ForeignKey("health_data.id"))

    risk_level = Column(String(20))  # critical, warning, mild
    type = Column(String(50))  # fall, heart_attack, etc.
    description = Column(Text)

    # 响应信息
    responded = Column(Boolean, default=False)
    response_actions = Column(Text)  # JSON存储响应动作
    response_time = Column(DateTime)

    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系 - 使用relationship而不是Column
    user = relationship("User", back_populates="emergency_events")
    health_data = relationship("HealthData", back_populates="emergency_events")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    name = Column(String(100))
    # 字段名从 relationship 改为 contact_relationship，避免命名冲突
    contact_relationship = Column(String(50))  # 关系：子女、配偶等
    phone_number = Column(String(20))
    email = Column(String(100))
    priority = Column(Integer, default=1)  # 联系优先级

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系 - 现在会正确引用 sqlalchemy.orm.relationship 函数
    user = relationship("User", back_populates="emergency_contacts")


# 健康数据创建模型（API接收数据时使用）
class HealthDataCreate(BaseModel):
    device_id: str
    device_type: str
    heart_rate: Optional[int] = None
    blood_oxygen: Optional[float] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    blood_glucose: Optional[float] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    steps: Optional[int] = None
    calories: Optional[float] = None
    distance: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    environment_temp: Optional[float] = None
    environment_humidity: Optional[float] = None
    timestamp: Optional[datetime] = None


# 健康数据响应模型（API返回数据时使用）
class HealthDataResponse(HealthDataCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# 紧急事件创建模型
class EmergencyEventCreate(BaseModel):
    health_data_id: Optional[int] = None
    risk_level: str = Field(..., pattern="^(critical|warning|mild)$")
    type: str
    description: str


# 紧急事件响应模型
class EmergencyEventResponse(EmergencyEventCreate):
    id: int
    user_id: int
    responded: bool
    response_actions: Optional[str] = None
    response_time: Optional[datetime] = None
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# 紧急联系人创建模型
class EmergencyContactCreate(BaseModel):
    name: str
    contact_relationship: str  # 注意这里与模型中的字段名一致
    phone_number: str
    email: Optional[str] = None
    priority: int = 1


# 紧急联系人响应模型
class EmergencyContactResponse(EmergencyContactCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True