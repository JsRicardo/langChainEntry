import os
import sys
import json
import logging
import requests
from typing import Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dependency_analysis_tester')

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DependencyAnalysisTester:
    """依赖分析功能测试器"""
    
    def __init__(self, webhook_url: str = 'http://localhost:8000/webhook/gitlab', gitlab_token: str = None):
        self.webhook_url = webhook_url
        self.gitlab_token = gitlab_token
        
    def create_test_payload(self, changed_files: list) -> Dict[str, Any]:
        """创建测试用的GitLab Webhook payload"""
        return {
            'event_name': 'push',
            'ref': 'refs/heads/main',
            'user_name': '测试用户',
            'project': {
                'name': '测试项目',
                'id': 123
            },
            'project_id': 123,
            'total_commits_count': 1,
            'commits': [
                {
                    'id': 'test-commit-id',
                    'message': '测试代码变更',
                    'timestamp': '2023-10-01T10:00:00Z',
                    'author': {
                        'name': '测试用户',
                        'email': 'test@example.com'
                    },
                    'added': [f for f in changed_files if 'new' in f],
                    'modified': [f for f in changed_files if 'modified' in f],
                    'removed': [f for f in changed_files if 'removed' in f]
                }
            ]
        }
    
    def send_test_webhook(self, payload: Dict[str, Any]) -> Dict:
        """发送测试Webhook请求"""
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            if self.gitlab_token:
                headers['X-Gitlab-Token'] = self.gitlab_token
            
            response = requests.post(
                self.webhook_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response_data = {
                'status_code': response.status_code,
                'content': response.text
            }
            
            logger.info(f"Webhook请求发送成功，状态码: {response.status_code}")
            return response_data
        except Exception as e:
            logger.error(f"Webhook请求发送失败: {str(e)}")
            return {
                'status_code': 500,
                'content': str(e)
            }
    
    def test_with_sample_files(self):
        """使用示例文件进行测试"""
        # 示例变更文件列表
        # 请根据您的实际项目结构修改这些文件路径
        sample_files = [
            # 测试修改的文件
            'src/api/webhook_receiver.py',
            'src/utils/dependency_analyzer.py',
            
            # 测试新增的文件
            'new_file.py'
        ]
        
        logger.info(f"开始测试依赖分析功能，测试文件: {sample_files}")
        
        # 创建测试payload
        payload = self.create_test_payload(sample_files)
        
        # 保存payload到文件，以便调试
        with open('test_webhook_payload.json', 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试payload已保存到 test_webhook_payload.json")
        
        # 发送测试Webhook请求
        response = self.send_test_webhook(payload)
        
        logger.info(f"测试完成，响应状态码: {response['status_code']}")
        logger.info(f"响应内容: {response['content']}")
        
        return response
    
    def run_interactive_test(self):
        """交互式测试"""
        print("=== 依赖分析功能测试器 ===")
        print("请输入要测试的文件路径，每行一个文件，输入空行结束:")
        
        changed_files = []
        while True:
            file_path = input().strip()
            if not file_path:
                break
            changed_files.append(file_path)
        
        if not changed_files:
            print("未输入任何文件路径，使用默认示例文件进行测试")
            return self.test_with_sample_files()
        
        logger.info(f"开始交互式测试，测试文件: {changed_files}")
        
        # 创建测试payload
        payload = self.create_test_payload(changed_files)
        
        # 保存payload到文件，以便调试
        with open('interactive_test_payload.json', 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试payload已保存到 interactive_test_payload.json")
        
        # 发送测试Webhook请求
        response = self.send_test_webhook(payload)
        
        logger.info(f"测试完成，响应状态码: {response['status_code']}")
        logger.info(f"响应内容: {response['content']}")
        
        return response

if __name__ == '__main__':
    tester = DependencyAnalysisTester()
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        tester.run_interactive_test()
    else:
        tester.test_with_sample_files()