# 通知模块初始化文件

from .wecom_service import WeComNotificationService, create_wecom_notification_service

__all__ = [
    "WeComNotificationService",
    "create_wecom_notification_service"
]