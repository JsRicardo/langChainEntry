import sys
import os

# 将项目根目录添加到Python搜索路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import unittest
import logging
from src.ai.assessment_service import AIAssessmentService, create_ai_assessment_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestAIAssessmentService(unittest.TestCase):
    
    def setUp(self):
        """测试前的准备工作"""
        logger.info("开始测试AI评估服务")
        self.assessment_service = create_ai_assessment_service()
        
        # 准备测试用的代码变更示例
        self.example_code_changes = """
# 修改了用户登录逻辑
```python
# src/services/auth_service.py

def login(username, password):
    # 原代码：简单的用户名密码验证
    # if username == "admin" and password == "password":
    #     return {"success": True, "token": "dummy_token"}
    # return {"success": False}
    
    # 新代码：增强的身份验证逻辑
    if not username or not password:
        return {"success": False, "error": "用户名和密码不能为空"}
        
    # 验证用户名格式
    if not isinstance(username, str) or len(username) < 3:
        return {"success": False, "error": "用户名格式不正确"}
        
    # 实际项目中会调用数据库验证
    if username == "admin" and password == "secure_password_123":
        return {"success": True, "token": "secure_jwt_token"}
    
    return {"success": False, "error": "用户名或密码错误"}
```
        """
        
        # 准备测试用的系统上下文
        self.example_system_context = """
系统信息：
- 项目名称：用户管理系统
- 主要模块：认证服务、用户管理、权限控制
- 关键依赖：JWT认证、数据库ORM框架
- 部署环境：开发、测试、生产
        """
    
    def test_create_service(self):
        """测试创建AI评估服务实例"""
        logger.info("测试：创建AI评估服务实例")
        service = create_ai_assessment_service()
        self.assertIsInstance(service, AIAssessmentService)
        logger.info("✓ 服务实例创建成功")
    
    def test_assess_code_changes(self):
        """测试代码变更评估功能"""
        logger.info("测试：代码变更评估功能")
        result = self.assessment_service.assess_code_changes(self.example_code_changes)
        
        self.assertIsInstance(result, str)
        self.assertNotEqual(len(result.strip()), 0)
        logger.info(f"✓ 代码变更评估完成，结果长度: {len(result)} 字符")
        logger.debug(f"评估结果示例: {result[:100]}...")
    
    def test_analyze_impact(self):
        """测试影响分析功能"""
        logger.info("测试：影响分析功能")
        result = self.assessment_service.analyze_impact(
            self.example_code_changes,
            self.example_system_context
        )
        
        self.assertIsInstance(result, str)
        self.assertNotEqual(len(result.strip()), 0)
        logger.info(f"✓ 影响分析完成，结果长度: {len(result)} 字符")
        logger.debug(f"分析结果示例: {result[:100]}...")
    
    def test_generate_combined_report(self):
        """测试综合报告生成功能"""
        logger.info("测试：综合报告生成功能")
        result = self.assessment_service.generate_combined_report(
            self.example_code_changes,
            self.example_system_context
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("code_change_assessment", result)
        self.assertIn("impact_analysis", result)
        self.assertIn("comprehensive_summary", result)  # 验证新增的综合总结字段
        
        # 验证每个报告部分都有内容
        self.assertIsInstance(result["code_change_assessment"], str)
        self.assertIsInstance(result["impact_analysis"], str)
        self.assertIsInstance(result["comprehensive_summary"], str)
        
        self.assertNotEqual(len(result["code_change_assessment"].strip()), 0)
        self.assertNotEqual(len(result["impact_analysis"].strip()), 0)
        self.assertNotEqual(len(result["comprehensive_summary"].strip()), 0)
        
        logger.info(f"✓ 综合报告生成完成")
        logger.debug(f"代码变更评估长度: {len(result['code_change_assessment'])} 字符")
        logger.debug(f"影响分析长度: {len(result['impact_analysis'])} 字符")
        logger.debug(f"综合总结长度: {len(result['comprehensive_summary'])} 字符")
    
    def test_empty_input_handling(self):
        """测试空输入的处理"""
        logger.info("测试：空输入的处理")
        
        # 测试空代码变更
        empty_result = self.assessment_service.assess_code_changes("")
        self.assertIsInstance(empty_result, str)
        logger.info(f"✓ 空代码变更处理结果: {empty_result}")
        
        # 测试空系统上下文
        no_context_result = self.assessment_service.analyze_impact(self.example_code_changes, "")
        self.assertIsInstance(no_context_result, str)
        self.assertNotEqual(len(no_context_result.strip()), 0)
        logger.info(f"✓ 空系统上下文处理成功")
        
        # 测试空输入的综合报告
        empty_report = self.assessment_service.generate_combined_report("", "")
        self.assertIsInstance(empty_report, dict)
        logger.info(f"✓ 空输入综合报告处理成功")
    
    def tearDown(self):
        """测试后的清理工作"""
        logger.info("AI评估服务测试完成")

if __name__ == "__main__":
    # 运行所有测试
    unittest.main()