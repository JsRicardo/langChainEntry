"""
AI模块初始化文件，导出AI评估服务的公共接口
"""

from .assessment_service import AIAssessmentService, create_ai_assessment_service

__all__ = [
    "AIAssessmentService",
    "create_ai_assessment_service"
]