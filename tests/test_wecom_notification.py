#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""企业微信通知服务测试"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.notification import WeComNotificationService
from src.config import ConfigManager


class TestWeComNotificationService(unittest.TestCase):
    """企业微信通知服务测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 使用模拟的Webhook URL
        self.webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test_key"
        # 创建通知服务实例
        self.notification_service = WeComNotificationService(self.webhook_url)
    
    def test_init_with_invalid_url(self):
        """测试使用无效URL初始化时的行为"""
        with self.assertRaises(ValueError):
            WeComNotificationService("")
    
    @patch('requests.post')
    def test_send_text_notification_success(self, mock_post):
        """测试成功发送文本通知"""
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
        mock_post.return_value = mock_response
        
        # 执行测试
        result = self.notification_service.send_text_notification("测试消息")
        
        # 验证结果
        self.assertEqual(result, {"errcode": 0, "errmsg": "ok"})
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], self.webhook_url)
        self.assertIn("Content-Type", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
    
    @patch('requests.post')
    def test_send_text_notification_with_mentions(self, mock_post):
        """测试发送带@的文本通知"""
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
        mock_post.return_value = mock_response
        
        # 执行测试
        mentioned_list = ["zhangsan", "lisi"]
        result = self.notification_service.send_text_notification(
            "测试消息", mentioned_list=mentioned_list
        )
        
        # 验证结果
        self.assertEqual(result, {"errcode": 0, "errmsg": "ok"})
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        import json
        payload = json.loads(kwargs["data"])
        self.assertEqual(payload["text"]["mentioned_list"], mentioned_list)
    
    @patch('requests.post')
    def test_send_markdown_notification_success(self, mock_post):
        """测试成功发送Markdown通知"""
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
        mock_post.return_value = mock_response
        
        # 执行测试
        markdown_content = "# 测试标题\n这是一条**Markdown**格式的测试消息。"
        result = self.notification_service.send_markdown_notification(markdown_content)
        
        # 验证结果
        self.assertEqual(result, {"errcode": 0, "errmsg": "ok"})
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        import json
        payload = json.loads(kwargs["data"])
        self.assertEqual(payload["markdown"]["content"], markdown_content)
    
    @patch('requests.post')
    def test_send_notification_request_exception(self, mock_post):
        """测试发送通知时发生请求异常"""
        # 配置模拟异常
        from requests.exceptions import RequestException
        mock_post.side_effect = RequestException("连接失败")
        
        # 执行测试并验证异常
        with self.assertRaises(RequestException):
            self.notification_service.send_text_notification("测试消息")
    
    def test_create_code_change_report(self):
        """测试创建代码变更报告"""
        # 准备测试数据
        commit_info = {
            "author": "张三",
            "time": "2023-05-15 14:30:22",
            "branch": "feature/login-optimization",
            "message": "优化登录页面性能"
        }
        
        file_changes = [
            {"path": "src/pages/Login/index.tsx", "type": "修改"},
            {"path": "src/components/Button/index.tsx", "type": "修改"},
            {"path": "src/utils/auth.ts", "type": "新增"}
        ]
        
        impact_analysis = {
            "affected_pages": ["登录页", "用户中心页"],
            "affected_components": ["登录表单", "按钮组件", "认证服务"],
            "impact_score": 50,
            "risk_points": [
                "登录流程可能出现异常",
                "按钮点击事件处理逻辑变更"
            ]
        }
        
        test_suggestions = [
            "验证登录功能正常",
            "测试按钮组件在不同场景下的表现"
        ]
        
        links = {
            "查看完整代码变更": "https://gitlab.example.com/project/-/merge_requests/123/diffs"
        }
        
        # 执行测试
        report = self.notification_service.create_code_change_report(
            commit_info, file_changes, impact_analysis, test_suggestions, links
        )
        
        # 验证结果
        self.assertIn("# 代码变更影响分析报告", report)
        self.assertIn("## 变更基本信息", report)
        self.assertIn("张三", report)
        self.assertIn("feature/login-optimization", report)
        self.assertIn("## 变更文件列表", report)
        self.assertIn("src/pages/Login/index.tsx", report)
        self.assertIn("## 影响范围分析", report)
        self.assertIn("**受影响页面**: 登录页、用户中心页", report)
        self.assertIn("**影响程度**: 中", report)
        self.assertIn("## 测试建议", report)
        self.assertIn("1. 验证登录功能正常", report)
        self.assertIn("## 关联信息", report)


if __name__ == "__main__":
    unittest.main()