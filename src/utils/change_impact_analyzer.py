import os
import logging
import re
from typing import Dict, List, Any, Optional
from src.utils.dependency_analyzer import DependencyAnalyzer
from src.ai.assessment_service import AIAssessmentService

logger = logging.getLogger(__name__)

class ChangeImpactAnalyzer:
    """代码变更影响分析器
    
    用于递归查询修改的文件被哪些页面引用，并集成AI分析生成测试用例
    """
    
    def __init__(self, project_root: str = None):
        self.dependency_analyzer = DependencyAnalyzer()
        if project_root:
            self.dependency_analyzer.set_project_root(project_root)
        self.ai_service = None
        
    def initialize_ai_service(self):
        """初始化AI评估服务"""
        try:
            self.ai_service = AIAssessmentService()
            logger.info("AI评估服务初始化成功")
        except Exception as e:
            logger.error(f"AI评估服务初始化失败: {str(e)}")
            # 创建一个模拟的AI服务以便在开发环境中继续
            self.ai_service = self._create_mock_ai_service()
    
    def _create_mock_ai_service(self):
        """创建模拟的AI服务"""
        class MockAIService:
            def assess_code_changes(self, code_changes_description: str) -> str:
                return "这是一个模拟的代码变更评估结果。"
            
            def analyze_impact(self, code_changes_description: str, system_context: str) -> Dict:
                return {
                    'risk_level': '低',
                    'module_impact': ['测试模块'],
                    'interface_impact': ['测试接口'],
                    'business_impact': '影响较小'
                }
            
            def generate_test_cases(self, code_changes_description: str) -> List[Dict]:
                return [
                    {
                        'name': '测试用例1',
                        'description': '验证代码变更是否按预期工作',
                        'steps': ['步骤1', '步骤2', '步骤3'],
                        'expected_result': '预期结果'
                    }
                ]
        
        return MockAIService()
    
    def build_dependency_graph(self, start_dir: str = None):
        """构建项目依赖图
        
        Args:
            start_dir: 开始分析的目录，默认为项目根目录
        """
        self.dependency_analyzer.analyze_project(start_dir)
    
    def find_pages_using_file(self, file_path: str, depth: int = 3) -> List[str]:
        """递归查询哪些页面引用了指定文件
        
        Args:
            file_path: 要查询的文件路径
            depth: 递归深度，默认为3层
            
        Returns:
            List[str]: 引用该文件的页面列表
        """
        # 标准化文件路径
        normalized_file_path = self.dependency_analyzer.normalize_path(file_path)
        
        # 查找直接依赖该文件的文件（反向依赖）
        dependent_files = self.dependency_analyzer.graph.get_dependents(normalized_file_path)
        
        # 递归查找更深层次的依赖
        all_dependent_files = set(dependent_files)
        current_level = dependent_files
        
        for _ in range(depth - 1):
            next_level = []
            for f in current_level:
                next_level.extend(self.dependency_analyzer.graph.get_dependents(f))
            
            # 过滤掉已经处理过的文件
            next_level = [f for f in next_level if f not in all_dependent_files]
            if not next_level:
                break
            
            all_dependent_files.update(next_level)
            current_level = next_level
        
        # 将集合转换为列表并返回
        return list(all_dependent_files)
    
    def find_pages_using_files(self, file_paths: List[str], depth: int = 3) -> Dict[str, List[str]]:
        """递归查询哪些页面引用了指定的多个文件
        
        Args:
            file_paths: 要查询的文件路径列表
            depth: 递归深度，默认为3层
            
        Returns:
            Dict[str, List[str]]: 文件路径到引用该文件的页面列表的映射
        """
        result = {}
        for file_path in file_paths:
            result[file_path] = self.find_pages_using_file(file_path, depth)
        
        return result
    
    def analyze_code_and_generate_tests(self, file_path: str) -> Dict[str, Any]:
        """分析代码并生成测试用例
        
        Args:
            file_path: 要分析的文件路径
            
        Returns:
            Dict[str, Any]: 分析结果和测试用例
        """
        if not self.ai_service:
            self.initialize_ai_service()
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
            
            # 构建代码变更描述
            file_name = os.path.basename(file_path)
            code_changes_description = f"文件: {file_name}\n内容:\n{file_content}"
            
            # 查找引用该文件的页面
            referencing_pages = self.find_pages_using_file(file_path)
            
            # 构建上下文信息
            system_context = f"这是一个代码变更分析任务。\n"
            system_context += f"被分析的文件: {file_name}\n"
            if referencing_pages:
                system_context += f"引用该文件的页面有 {len(referencing_pages)} 个: {', '.join(referencing_pages[:5])}{'...' if len(referencing_pages) > 5 else ''}\n"
            
            # 使用AI分析代码变更
            assessment_result = self.ai_service.assess_code_changes(code_changes_description)
            impact_analysis = self.ai_service.analyze_impact(code_changes_description, system_context)
            
            # 生成测试用例
            test_cases = self._extract_test_cases_from_impact_analysis(impact_analysis)
            
            return {
                'file_path': file_path,
                'referencing_pages': referencing_pages,
                'assessment_result': assessment_result,
                'impact_analysis': impact_analysis,
                'test_cases': test_cases
            }
        except Exception as e:
            logger.error(f"分析文件 {file_path} 时出错: {str(e)}")
            return {
                'file_path': file_path,
                'error': str(e)
            }
            
    def _extract_test_cases_from_impact_analysis(self, impact_analysis: str) -> List[Dict[str, str]]:
        """从影响分析结果中提取测试用例建议
        
        Args:
            impact_analysis: 影响分析结果字符串
            
        Returns:
            List[Dict[str, str]]: 测试用例列表
        """
        try:
            # 初始化默认测试用例
            default_test_cases = [{
                'name': '基本功能测试',
                'description': '验证代码的基本功能是否正常工作',
                'steps': ['执行代码', '观察结果', '验证是否符合预期'],
                'expected_result': '功能正常执行，无错误'
            }]
            
            if not impact_analysis:
                return default_test_cases
            
            # 从影响分析中提取测试相关信息
            # 检查是否有明确的测试建议部分
            if '测试建议' in impact_analysis:
                # 提取测试建议部分
                test_suggestions_match = re.search(r'测试建议：?\s*(.*?)(?:\n##|$)', impact_analysis, re.DOTALL)
                if test_suggestions_match:
                    test_suggestions = test_suggestions_match.group(1).strip()
                    if test_suggestions:
                        # 根据测试建议创建测试用例
                        return [{
                            'name': 'AI建议的测试用例',
                            'description': f'基于AI分析的测试建议：{test_suggestions}',
                            'steps': ['根据测试建议准备测试环境', '执行测试操作', '验证测试结果'],
                            'expected_result': '测试通过，无异常情况'
                        }]
            
            # 检查是否有测试重点或测试策略部分
            if '测试重点' in impact_analysis:
                test_focus_match = re.search(r'测试重点：?\s*(.*?)(?:\n##|$)', impact_analysis, re.DOTALL)
                if test_focus_match:
                    test_focus = test_focus_match.group(1).strip()
                    if test_focus:
                        return [{
                            'name': '重点测试用例',
                            'description': f'测试重点：{test_focus}',
                            'steps': ['准备重点测试场景', '执行测试', '验证关键功能'],
                            'expected_result': '重点功能正常运行'
                        }]
            
            # 如果没有找到特定的测试建议，返回默认测试用例
            return default_test_cases
        except Exception as e:
            logger.error(f"提取测试用例失败: {str(e)}")
            return [{
                'name': '默认测试用例',
                'description': '验证代码功能正常',
                'steps': ['运行代码', '检查输出'],
                'expected_result': '功能正常'
            }]
    
    def batch_analyze_and_generate_tests(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量分析文件并生成测试用例
        
        Args:
            file_paths: 要分析的文件路径列表
            
        Returns:
            Dict[str, Dict[str, Any]]: 文件路径到分析结果的映射
        """
        results = {}
        for file_path in file_paths:
            results[file_path] = self.analyze_code_and_generate_tests(file_path)
        
        return results