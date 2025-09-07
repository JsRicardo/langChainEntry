#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""企业微信通知发送示例"""

import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import init_config, get_config
from src.notification import WeComNotificationService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """示例主函数"""
    # 初始化配置
    init_config()
    
    # 获取企业微信Webhook URL
    # 注意：在实际使用时，建议通过环境变量设置，而不是直接硬编码
    webhook_url = get_config("notification.wecom.webhook_url")
    
    # 如果配置中没有Webhook URL，尝试从环境变量获取
    if not webhook_url:
        webhook_url = os.environ.get("WECOM_WEBHOOK_URL")
    
    # 如果还是没有Webhook URL，提示用户
    if not webhook_url:
        logger.error("未配置企业微信Webhook URL，请在配置文件或环境变量中设置")
        logger.info("示例将使用模拟数据演示消息格式")
        # 创建模拟服务用于演示
        class MockWeComService:
            def send_markdown_notification(self, markdown_content, mentioned_list=None):
                logger.info(f"\n\n--- 模拟发送Markdown通知 ---\n{markdown_content}\n\n--- 通知结束 ---")
                return {"errcode": 0, "errmsg": "ok"}
            
            def send_text_notification(self, text, mentioned_list=None):
                logger.info(f"\n\n--- 模拟发送文本通知 ---\n{text}\n\n--- 通知结束 ---")
                return {"errcode": 0, "errmsg": "ok"}
        
        wecom_service = MockWeComService()
    else:
        # 创建企业微信通知服务实例
        wecom_service = WeComNotificationService(webhook_url)
    
    try:
        # 演示1：发送简单文本消息
        logger.info("发送简单文本消息...")
        wecom_service.send_text_notification(
            "这是一条来自代码变更分析系统的测试消息！\n\n系统已成功初始化。",
            mentioned_list=["@all"]  # @所有人
        )
        
        # 演示2：发送代码变更分析报告（Markdown格式）
        logger.info("发送代码变更分析报告...")
        
        # 模拟提交信息
        commit_info = {
            "author": "张三",
            "time": "2023-05-15 14:30:22",
            "branch": "feature/login-optimization",
            "message": "优化登录页面性能"
        }
        
        # 模拟文件变更
        file_changes = [
            {"path": "src/pages/Login/index.tsx", "type": "修改"},
            {"path": "src/components/Button/index.tsx", "type": "修改"},
            {"path": "src/utils/auth.ts", "type": "新增"}
        ]
        
        # 模拟影响分析
        impact_analysis = {
            "affected_pages": ["登录页", "用户中心页"],
            "affected_components": ["登录表单", "按钮组件", "认证服务"],
            "impact_score": 50,
            "risk_points": [
                "登录流程可能出现异常",
                "按钮点击事件处理逻辑变更",
                "认证逻辑修改可能影响用户会话管理"
            ]
        }
        
        # 模拟测试建议
        test_suggestions = [
            "验证登录功能正常，包括账号密码登录和第三方登录",
            "测试按钮组件在不同场景下的表现",
            "检查用户会话管理是否稳定"
        ]
        
        # 模拟相关链接
        links = {
            "查看完整代码变更": "https://gitlab.example.com/project/-/merge_requests/123/diffs",
            "查看流水线状态": "https://gitlab.example.com/project/-/pipelines/456"
        }
        
        # 创建Markdown格式报告
        report = wecom_service.create_code_change_report(
            commit_info, file_changes, impact_analysis, test_suggestions, links
        )
        
        # 发送报告
        wecom_service.send_markdown_notification(report)
        
        logger.info("所有示例消息发送完成！")
        
    except Exception as e:
        logger.error(f"发送通知时出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()