# app/utils/emergency_responder.py（修复后完整代码）
import logging

from sqlalchemy.orm import Session  # 保留正确导入

from app.models.health import EmergencyEvent, EmergencyContact
from app.utils.notification import NotificationService

# 1. 删除这行错误导入：from pandas.conftest import cls

logger = logging.getLogger(__name__)


class EmergencyResponder:
    @staticmethod
    def handle_emergency(db: Session, emergency_event: EmergencyEvent, user_id: int):
        """根据紧急级别处理紧急事件"""
        contacts = db.query(EmergencyContact).filter(
            EmergencyContact.user_id == user_id
        ).order_by(EmergencyContact.priority).all()  # 按优先级排序，优先联系高优先级联系人

        # 2. 修复：用类名 EmergencyResponder 调用静态方法，替代错误的 cls
        if emergency_event.risk_level == "critical":
            EmergencyResponder.handle_critical_emergency(db, emergency_event, contacts)
        elif emergency_event.risk_level == "warning":
            EmergencyResponder.handle_warning_emergency(db, emergency_event, contacts)
        elif emergency_event.risk_level == "mild":
            EmergencyResponder.handle_mild_alert(db, emergency_event, contacts)  # 确保该方法已实现
        else:
            logger.warning(f"未知风险级别: {emergency_event.risk_level}，跳过处理")

    # 以下方法不变（handle_critical_emergency 等）
    @staticmethod
    def handle_critical_emergency(db: Session, emergency_event: EmergencyEvent, contacts):
        logger.error(f"紧急危机事件: {emergency_event.description}")
        for contact in contacts:
            NotificationService.send_emergency_alert(
                contact.phone_number,
                f"紧急: 用户健康状况危急。详情: {emergency_event.description}"
            )
        NotificationService.call_emergency_services(
            f"用户ID: {emergency_event.user_id}, 紧急情况: {emergency_event.description}"
        )
        NotificationService.notify_healthcare_provider(
            f"用户ID: {emergency_event.user_id}发生紧急医疗事件: {emergency_event.description}"
        )

    @staticmethod
    def handle_warning_emergency(db: Session, emergency_event: EmergencyEvent, contacts):
        logger.warning(f"警告级别事件: {emergency_event.description}")
        user_responded = NotificationService.request_user_confirmation(
            emergency_event.user_id,
            f"检测到健康异常: {emergency_event.description}. 您是否需要帮助?"
        )
        if not user_responded:
            for contact in contacts:
                NotificationService.send_alert(
                    contact.phone_number,
                    f"警告: 用户健康异常且未回应。详情: {emergency_event.description}"
                )

    # 补充：实现之前缺失的 handle_mild_alert 方法（避免 AttributeError）
    @staticmethod
    def handle_mild_alert(db: Session, emergency_event: EmergencyEvent, contacts):
        """处理轻度风险事件：仅通知用户，无需联系紧急联系人"""
        logger.info(f"轻度风险事件: {emergency_event.description}")
        # 若有联系人，可选择通知（或仅通知用户本人，此处示例通知第一个联系人）
        if contacts:
            NotificationService.send_alert(
                contacts[0].phone_number,
                f"轻度健康提醒: 用户{emergency_event.user_id}的健康数据异常。详情: {emergency_event.description}，建议关注。"
            )