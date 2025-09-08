# app/services/health_monitor.py

import logging

from fastapi import BackgroundTasks
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.health_agent.emergency_responder import EmergencyResponder
from app.health_agent.risk_analyzer import RiskAnalyzer
from app.models.health import HealthData, EmergencyEvent, EmergencyContact, EmergencyContactCreate
# 导入Pydantic模型
from app.models.health import (
    HealthDataCreate, EmergencyEventCreate
)

logger = logging.getLogger(__name__)


class HealthMonitorService:
    @staticmethod
    def create_health_data(db: Session, health_data: HealthDataCreate, user_id: int):
        """存储健康数据并分析风险"""
        # 存储数据
        db_health_data = HealthData(**health_data.dict(), user_id=user_id)
        db.add(db_health_data)
        db.commit()
        db.refresh(db_health_data)

        # 分析风险
        risk_level = RiskAnalyzer.analyze(db_health_data)

        # 如果检测到风险，创建紧急事件
        if risk_level != "normal":
            emergency_data = EmergencyEventCreate(
                health_data_id=db_health_data.id,
                risk_level=risk_level,
                # 根据实际检测到的异常类型设置具体值
                type="abnormal_heart_rate" if health_data.heart_rate else
                "high_blood_pressure" if (health_data.systolic_bp or health_data.diastolic_bp) else
                "health_risk",  # 默认类型
                description=f"健康数据检测到{risk_level}级别风险"
            )
            emergency_event = EmergencyEvent(
                **emergency_data.dict(),
                user_id=user_id
            )
            db.add(emergency_event)
            db.commit()

            # 触发紧急响应
            EmergencyResponder.handle_emergency(db, emergency_event, user_id)

        return db_health_data

    @staticmethod
    def handle_emergency(db: Session, background_tasks: BackgroundTasks,
                         emergency_data: EmergencyEventCreate, user_id: int):
        """处理紧急事件"""
        emergency_event = EmergencyEvent(**emergency_data.dict(), user_id=user_id)
        db.add(emergency_event)
        db.commit()
        db.refresh(emergency_event)

        # 在后台处理紧急响应
        background_tasks.add_task(
            EmergencyResponder.handle_emergency,
            db, emergency_event, user_id
        )

        return emergency_event

    @staticmethod
    def add_emergency_contact(db: Session, contact: EmergencyContactCreate, user_id: int):
        """添加紧急联系人"""
        db_contact = EmergencyContact(**contact.dict(), user_id=user_id)
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact

    @staticmethod
    def get_user_health_data(db: Session, user_id: int, skip: int = 0, limit: int = 100):
        return db.query(HealthData).filter(
            HealthData.user_id == user_id
        ).order_by(desc(HealthData.timestamp)).offset(skip).limit(limit).all()

    # 新增：获取紧急事件详情（验证用户权限）
    @staticmethod
    def get_emergency_event(db: Session, event_id: int, user_id: int):
        event = db.query(EmergencyEvent).filter(
            EmergencyEvent.id == event_id,
            EmergencyEvent.user_id == user_id
        ).first()
        if not event:
            raise ValueError("紧急事件不存在或无访问权限")
        return event

    # 新增：获取用户所有紧急联系人
    @staticmethod
    def get_emergency_contacts(db: Session, user_id: int):
        return db.query(EmergencyContact).filter(
            EmergencyContact.user_id == user_id
        ).order_by(EmergencyContact.priority).all()

    # 新增：获取用户最新健康数据（用于前端实时展示）
    @staticmethod
    def get_latest_health_data(db: Session, user_id: int):
        return db.query(HealthData).filter(
            HealthData.user_id == user_id
        ).order_by(desc(HealthData.timestamp)).first()

