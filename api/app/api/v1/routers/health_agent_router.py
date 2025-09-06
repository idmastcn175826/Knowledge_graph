# app/api/v1/routers/health.py
from typing import List

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.health_agent.health_monitor import HealthMonitorService
from app.models.health import HealthDataResponse, HealthDataCreate, \
    EmergencyEventResponse, EmergencyEventCreate, EmergencyContactResponse, EmergencyContactCreate
from app.utils.auth import get_current_user

router = APIRouter()

@router.post("/health-data", response_model=HealthDataResponse)
async def create_health_data(
    health_data: HealthDataCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """接收健康设备上传的数据"""
    return HealthMonitorService.create_health_data(db, health_data, current_user.id)

@router.get("/health-data", response_model=List[HealthDataResponse])
async def get_health_data(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取用户健康数据"""
    return HealthMonitorService.get_user_health_data(db, current_user["id"], skip, limit)

@router.post("/emergency", response_model=EmergencyEventResponse)
async def trigger_emergency(
    background_tasks: BackgroundTasks,
    emergency_data: EmergencyEventCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """触发紧急事件"""
    return HealthMonitorService.handle_emergency(
        db, background_tasks, emergency_data, current_user.id
    )

@router.get("/emergency/{event_id}", response_model=EmergencyEventResponse)
async def get_emergency_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取紧急事件详情"""
    return HealthMonitorService.get_emergency_event(db, event_id, current_user.id)

@router.post("/emergency-contacts", response_model=EmergencyContactResponse)
async def add_emergency_contact(
    contact: EmergencyContactCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """添加紧急联系人"""
    return HealthMonitorService.add_emergency_contact(db, contact, current_user.id)

@router.get("/emergency-contacts", response_model=List[EmergencyContactResponse])
async def get_emergency_contacts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取用户紧急联系人列表"""
    return HealthMonitorService.get_emergency_contacts(db, current_user["id"])