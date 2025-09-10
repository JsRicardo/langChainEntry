import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.change_impact_analyzer import ChangeImpactAnalyzer

class TestChangeImpactAnalyzer(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        self.analyzer = ChangeImpactAnalyzer()
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.analyzer.dependency_analyzer.set_project_root(self.project_root)
    
    @patch('src.utils.dependency_analyzer.DependencyAnalyzer.graph')
    def test_find_pages_using_file(self, mock_graph):
        """测试查找引用指定文件的页面功能"""
        # 模拟依赖图的行为
        mock_graph.get_dependents.side_effect = [
            ['file1.py', 'file2.py'],  # 第一层依赖
            ['file3.py'],             # file1.py的依赖
            []                        # file2.py的依赖
        ]
        
        # 测试递归深度为2
        result = self.analyzer.find_pages_using_file('test_file.py', depth=2)
        
        # 验证结果
        expected = ['file1.py', 'file2.py', 'file3.py']
        self.assertEqual(set(result), set(expected))
        
        # 验证调用了正确的方法
        self.assertEqual(mock_graph.get_dependents.call_count, 3)
    
    @patch('src.utils.change_impact_analyzer.ChangeImpactAnalyzer.find_pages_using_file')
    def test_find_pages_using_files(self, mock_find_pages):
        """测试查找引用多个指定文件的页面功能"""
        # 模拟单个文件查找的行为
        mock_find_pages.side_effect = [
            ['file1.py', 'file2.py'],  # file1的依赖
            ['file3.py', 'file4.py']   # file2的依赖
        ]
        
        # 测试多个文件查找
        result = self.analyzer.find_pages_using_files(['file1.py', 'file2.py'], depth=1)
        
        # 验证结果
        self.assertEqual(result['file1.py'], ['file1.py', 'file2.py'])
        self.assertEqual(result['file2.py'], ['file3.py', 'file4.py'])
        
        # 验证调用了正确的方法
        self.assertEqual(mock_find_pages.call_count, 2)
    
    @patch('src.utils.change_impact_analyzer.AIAssessmentService')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='test code content')
    @patch('src.utils.change_impact_analyzer.ChangeImpactAnalyzer.find_pages_using_file')
    def test_analyze_code_and_generate_tests(self, mock_find_pages, mock_open, mock_ai_service):
        """测试分析代码并生成测试用例功能"""
        # 模拟查找页面的行为
        mock_find_pages.return_value = ['page1.py', 'page2.py']
        
        # 模拟AI服务的行为
        mock_ai_instance = mock_ai_service.return_value
        mock_ai_instance.assess_code_changes.return_value = '测试评估结果'
        mock_ai_instance.analyze_impact.return_value = '## 测试建议\n- 测试建议内容'
        
        # 测试分析代码功能
        result = self.analyzer.analyze_code_and_generate_tests('test_file.py')
        
        # 验证结果
        self.assertEqual(result['file_path'], 'test_file.py')
        self.assertEqual(result['referencing_pages'], ['page1.py', 'page2.py'])
        self.assertEqual(result['assessment_result'], '测试评估结果')
        self.assertEqual(result['impact_analysis'], '## 测试建议\n- 测试建议内容')
        
        # 验证测试用例是否生成
        self.assertGreaterEqual(len(result['test_cases']), 1)
        self.assertIn('name', result['test_cases'][0])
        self.assertIn('description', result['test_cases'][0])
        self.assertIn('steps', result['test_cases'][0])
        self.assertIn('expected_result', result['test_cases'][0])
    
    @patch('src.utils.change_impact_analyzer.ChangeImpactAnalyzer.analyze_code_and_generate_tests')
    def test_batch_analyze_and_generate_tests(self, mock_analyze):
        """测试批量分析代码并生成测试用例功能"""
        # 模拟单个文件分析的行为
        mock_analyze.side_effect = [
            {'file_path': 'file1.py', 'test_cases': [{'name': 'test1'}]},
            {'file_path': 'file2.py', 'test_cases': [{'name': 'test2'}]}
        ]
        
        # 测试批量分析
        result = self.analyzer.batch_analyze_and_generate_tests(['file1.py', 'file2.py'])
        
        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertIn('file1.py', result)
        self.assertIn('file2.py', result)
        self.assertEqual(result['file1.py']['test_cases'][0]['name'], 'test1')
        self.assertEqual(result['file2.py']['test_cases'][0]['name'], 'test2')
    
    def test_extract_test_cases_from_impact_analysis_with_suggestions(self):
        """测试从包含测试建议的影响分析结果中提取测试用例"""
        # 准备测试数据
        impact_analysis = """
        ## 模块影响
        - 模块1
        - 模块2
        
        ## 测试建议
        - 执行单元测试
        - 测试边界条件
        
        ## 其他部分
        其他内容
        """
        
        # 执行测试
        result = self.analyzer._extract_test_cases_from_impact_analysis(impact_analysis)
        
        # 验证结果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'AI建议的测试用例')
        self.assertIn('测试建议', result[0]['description'])
    
    def test_extract_test_cases_from_impact_analysis_with_focus(self):
        """测试从包含测试重点的影响分析结果中提取测试用例"""
        # 准备测试数据
        impact_analysis = """
        ## 接口影响
        - 接口1
        
        ## 测试重点
        重点测试接口1的性能和稳定性
        
        ## 风险等级
        中
        """
        
        # 执行测试
        result = self.analyzer._extract_test_cases_from_impact_analysis(impact_analysis)
        
        # 验证结果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], '重点测试用例')
        self.assertIn('测试重点', result[0]['description'])
    
    def test_extract_test_cases_from_impact_analysis_default(self):
        """测试从没有特定测试建议的影响分析结果中提取默认测试用例"""
        # 准备测试数据
        impact_analysis = """
        ## 模块影响
        - 模块1
        
        ## 业务影响
        业务影响较小
        
        ## 风险等级
        低
        """
        
        # 执行测试
        result = self.analyzer._extract_test_cases_from_impact_analysis(impact_analysis)
        
        # 验证结果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], '基本功能测试')
    
    def test_extract_test_cases_from_empty_impact_analysis(self):
        """测试从空的影响分析结果中提取测试用例"""
        # 执行测试
        result = self.analyzer._extract_test_cases_from_impact_analysis('')
        
        # 验证结果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], '基本功能测试')

if __name__ == '__main__':
    unittest.main()