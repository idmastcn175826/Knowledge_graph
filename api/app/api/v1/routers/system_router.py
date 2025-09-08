from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config.config import settings
from app.utils.auth import get_current_user

router = APIRouter()

# 存储健康监测状态（内存中）
health_monitor_status = {
    "enabled": settings.HEALTH_MONITOR_DEFAULT_ENABLED  # 从配置获取默认值
}


class ToggleRequest(BaseModel):
    enabled: bool


@router.get("/health-monitor/status", summary="获取健康监测状态")
async def get_health_monitor_status(current_user=Depends(get_current_user)):
    """获取当前健康监测功能的启用状态"""
    return {
        "enabled": health_monitor_status["enabled"],
        "message": "健康监测已开启" if health_monitor_status["enabled"] else "健康监测已关闭"
    }


@router.post("/health-monitor/toggle", summary="切换健康监测状态")
async def toggle_health_monitor(
        request: ToggleRequest,
        current_user=Depends(get_current_user)
):
    """开启或关闭健康监测功能"""
    # 如果需要权限控制，可以在这里添加
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="权限不足")

    health_monitor_status["enabled"] = request.enabled
    return {
        "enabled": health_monitor_status["enabled"],
        "message": f"健康监测已{'开启' if request.enabled else '关闭'}"
    }
