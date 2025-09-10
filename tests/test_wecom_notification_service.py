import unittest
import sys
import os
import json
from unittest import mock
from typing import Dict, List, Any

# 添加项目根目录到Python搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.notification.wecom_service import (
    WeComNotificationService,
    create_wecom_notification_service,
    MockWeComNotificationService
)

class TestWeComNotificationService(unittest.TestCase):
    
    def setUp(self):
        # 设置测试用的Webhook URL
        self.mock_webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=dummy_key"
        self.service = WeComNotificationService(self.mock_webhook_url)
        
        # 准备测试数据
        self.test_commit_info = {
            "author": "张三",
            "timestamp": "2023-10-15 14:30:00",
            "message": "修复登录页面的bug",
            "branch": "feature/login-fix"
        }
        
        self.test_file_changes = [
            {"path": "src/pages/LoginPage.py", "status": "modified"},
            {"path": "src/components/LoginForm.py", "status": "modified"},
            {"path": "tests/test_login.py", "status": "added"}
        ]
        
        self.test_impact_analysis = {
            "risk_level": "低",
            "module_impact": ["用户认证模块"],
            "interface_impact": ["登录接口"],
            "business_impact": "影响用户登录体验，但不影响核心业务流程"
        }
        
        self.test_test_suggestions = [
            "测试不同浏览器下的登录功能",
            "测试错误密码输入的错误提示",
            "测试登录成功后的跳转逻辑"
        ]
        
        self.test_links = {
            "GitLab提交": "https://gitlab.example.com/project/-/commit/123456",
            "相关Jira": "https://jira.example.com/browse/PROJ-123"
        }
    
    @mock.patch('src.notification.wecom_service.requests.post')
    def test_send_markdown_notification(self, mock_post):
        """测试发送Markdown格式通知"""
        # 配置mock响应
        mock_response = mock.Mock()
        mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
        mock_post.return_value = mock_response
        
        # 执行测试
        markdown_content = "# 测试标题\n这是测试内容"
        result = self.service.send_markdown_notification(markdown_content, ["user1"])
        
        # 验证结果
        self.assertEqual(result, {"errcode": 0, "errmsg": "ok"})
        mock_post.assert_called_once()
        
        # 验证请求参数
        called_args = mock_post.call_args
        self.assertEqual(called_args[0][0], self.mock_webhook_url)
        self.assertEqual(called_args[1]["headers"], {"Content-Type": "application/json"})
        
        # 验证请求体 - 解析JSON后再进行断言，避免中文转义问题
        request_body = called_args[1]["data"]
        parsed_body = json.loads(request_body)
        self.assertIn("测试标题", parsed_body["markdown"]["content"])
        self.assertIn("user1", parsed_body["markdown"]["mentioned_list"])
    
    @mock.patch('src.notification.wecom_service.requests.post')
    def test_send_text_notification(self, mock_post):
        """测试发送文本格式通知"""
        # 配置mock响应
        mock_response = mock.Mock()
        mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
        mock_post.return_value = mock_response
        
        # 执行测试
        text_content = "这是一条测试文本消息"
        result = self.service.send_text_notification(text_content)
        
        # 验证结果
        self.assertEqual(result, {"errcode": 0, "errmsg": "ok"})
        mock_post.assert_called_once()
        
        # 验证请求体 - 解析JSON后再进行断言
        called_args = mock_post.call_args
        request_body = called_args[1]["data"]
        parsed_body = json.loads(request_body)
        self.assertIn("这是一条测试文本消息", parsed_body["text"]["content"])
    
    def test_create_code_change_report(self):
        """测试创建代码变更分析报告"""
        # 执行测试
        report = self.service.create_code_change_report(
            self.test_commit_info,
            self.test_file_changes,
            self.test_impact_analysis,
            self.test_test_suggestions,
            self.test_links
        )
        
        # 验证报告内容
        self.assertIn("# 代码变更分析报告", report)
        self.assertIn("## 提交信息", report)
        self.assertIn("张三", report)  # 提交人
        self.assertIn("## 文件变更", report)
        self.assertIn("LoginPage.py", report)  # 文件名
        self.assertIn("## 影响分析", report)
        self.assertIn("✅ 低", report)  # 风险等级
        self.assertIn("## 测试建议", report)
        self.assertIn("测试不同浏览器下的登录功能", report)  # 测试建议
        self.assertIn("## 相关链接", report)
        self.assertIn("GitLab提交", report)  # 链接名称
        self.assertIn("报告生成时间", report)  # 生成时间
    
    def test_create_code_change_report_empty_data(self):
        """测试使用空数据创建报告"""
        # 执行测试
        report = self.service.create_code_change_report(
            {}, [], {}, [], {}
        )
        
        # 验证报告内容
        self.assertIn("# 代码变更分析报告", report)
        self.assertIn("未知", report)  # 未知信息
        self.assertIn("暂无文件变更", report)
        self.assertIn("暂无影响分析结果", report)
        self.assertIn("暂无测试建议", report)
    
    @mock.patch('src.config.config_manager.get_config')
    @mock.patch('src.config.config_manager.init_config')
    def test_create_wecom_notification_service_with_config(self, mock_init_config, mock_get_config):
        """测试从配置创建企业微信通知服务"""
        # 配置mock
        mock_get_config.return_value = self.mock_webhook_url
        
        # 执行测试
        service = create_wecom_notification_service()
        
        # 验证结果
        mock_init_config.assert_called_once()
        mock_get_config.assert_called_once_with("notification.wecom.webhook_url")
        self.assertIsInstance(service, WeComNotificationService)
    
    @mock.patch('src.config.config_manager.get_config')
    @mock.patch('src.config.config_manager.init_config')
    @mock.patch.dict('os.environ', {'WECOM_WEBHOOK_URL': 'https://example.com/webhook'})
    def test_create_wecom_notification_service_with_env(self, mock_init_config, mock_get_config):
        """测试从环境变量创建企业微信通知服务"""
        # 配置mock - 配置返回None
        mock_get_config.return_value = None
        
        # 执行测试
        service = create_wecom_notification_service()
        
        # 验证结果
        mock_get_config.assert_called_once_with("notification.wecom.webhook_url")
        self.assertIsInstance(service, WeComNotificationService)
    
    @mock.patch('src.config.config_manager.get_config')
    @mock.patch('src.config.config_manager.init_config')
    @mock.patch.dict('os.environ', clear=True)
    def test_create_wecom_notification_service_mock(self, mock_init_config, mock_get_config):
        """测试创建模拟的企业微信通知服务"""
        # 配置mock - 配置返回None
        mock_get_config.return_value = None
        
        # 执行测试
        service = create_wecom_notification_service()
        
        # 验证结果
        self.assertIsInstance(service, MockWeComNotificationService)
    
    @mock.patch('src.config.config_manager.get_config')
    @mock.patch('src.config.config_manager.init_config')
    def test_create_wecom_notification_service_exception(self, mock_init_config, mock_get_config):
        """测试创建企业微信通知服务时发生异常"""
        # 配置mock - 抛出异常
        mock_get_config.side_effect = Exception("配置错误")
        
        # 执行测试 - 不应该抛出异常
        service = create_wecom_notification_service()
        
        # 验证结果 - 应该返回模拟服务
        self.assertIsInstance(service, MockWeComNotificationService)

if __name__ == '__main__':
    unittest.main()