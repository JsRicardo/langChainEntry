import os
import sys
import logging
import requests

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeImpactAnalyzerDemo:
    """代码变更影响分析器演示类"""
    
    def __init__(self, api_url="http://localhost:8000"):
        """初始化演示类
        
        Args:
            api_url: API服务地址，默认为本地开发服务器地址
        """
        self.api_url = api_url
    
    def find_example_files(self) -> list:
        """查找项目中的示例文件
        
        Returns:
            list: 文件路径列表
        """
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 查找一些示例Python文件
        example_files = []
        
        # 遍历src目录查找Python文件
        for root, _, files in os.walk(os.path.join(project_root, "src")):
            for file in files:
                if file.endswith(".py") and "__init__.py" not in file:
                    file_path = os.path.join(root, file)
                    # 只添加较小的文件用于演示
                    if os.path.getsize(file_path) < 10000:  # 小于10KB
                        example_files.append(file_path)
                        # 只收集前3个文件用于演示
                        if len(example_files) >= 3:
                            break
            if len(example_files) >= 3:
                break
        
        return example_files
    
    def analyze_files_using_api(self, file_paths: list, depth: int = 3) -> dict:
        """使用API分析文件
        
        Args:
            file_paths: 文件路径列表
            depth: 递归查询深度
            
        Returns:
            dict: 分析结果
        """
        try:
            endpoint = f"{self.api_url}/api/analyze-code-impact"
            
            # 准备请求参数
            params = {
                "depth": depth
            }
            
            # 准备请求体（使用JSON格式）
            data = {"file_paths": file_paths}
            
            logger.info(f"发送请求到API: {endpoint}, 文件数量: {len(file_paths)}, 深度: {depth}")
            
            # 发送请求
            response = requests.post(endpoint, params=params, json=data)
            
            # 检查响应状态
            if response.status_code == 200:
                logger.info("API请求成功")
                return response.json()
            else:
                logger.error(f"API请求失败: {response.status_code}, {response.text}")
                return {
                    "status": "error",
                    "code": response.status_code,
                    "message": response.text
                }
        except Exception as e:
            logger.error(f"调用API时出错: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def display_results(self, results: dict):
        """显示分析结果
        
        Args:
            results: 分析结果字典
        """
        if not results or results.get("status") != "success":
            logger.error(f"分析失败: {results.get('message')}")
            return
        
        logger.info(f"分析成功: {results.get('message')}")
        
        # 获取结果数据
        analysis_results = results.get("results", {})
        
        for file_path, result in analysis_results.items():
            logger.info(f"\n文件: {file_path}")
            
            # 显示引用该文件的页面
            referencing_pages = result.get("referencing_pages", [])
            if referencing_pages:
                logger.info(f"引用该文件的页面数量: {len(referencing_pages)}")
                for page in referencing_pages[:3]:  # 只显示前3个页面
                    logger.info(f"  - {page}")
                if len(referencing_pages) > 3:
                    logger.info(f"  ... 还有 {len(referencing_pages) - 3} 个页面省略")
            else:
                logger.info("没有找到引用该文件的页面")
            
            # 显示测试用例
            test_cases = result.get("test_cases", [])
            if test_cases:
                logger.info(f"生成的测试用例数量: {len(test_cases)}")
                for i, test_case in enumerate(test_cases[:2]):  # 只显示前2个测试用例
                    logger.info(f"  测试用例 {i+1}:")
                    logger.info(f"    名称: {test_case.get('name')}")
                    logger.info(f"    描述: {test_case.get('description')}")
                    logger.info(f"    步骤: {', '.join(test_case.get('steps', []))}")
                    logger.info(f"    预期结果: {test_case.get('expected_result')}")
            else:
                logger.info("未生成测试用例")
            
            # 显示错误信息（如果有）
            if "error" in result:
                logger.error(f"错误: {result['error']}")

    def run_demo(self):
        """运行演示"""
        logger.info("代码变更影响分析器演示开始")
        
        # 查找示例文件
        example_files = self.find_example_files()
        if not example_files:
            logger.error("没有找到合适的示例文件")
            return
        
        logger.info(f"找到 {len(example_files)} 个示例文件用于演示")
        for file_path in example_files:
            logger.info(f"  - {file_path}")
        
        # 使用API分析文件
        results = self.analyze_files_using_api(example_files)
        
        # 显示结果
        self.display_results(results)
        
        logger.info("代码变更影响分析器演示结束")

if __name__ == "__main__":
    # 创建演示实例
    demo = CodeImpactAnalyzerDemo()
    
    # 运行演示
    demo.run_demo()