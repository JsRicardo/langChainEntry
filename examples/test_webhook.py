#!/usr/bin/env python3
import os
import sys
import json
import requests
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 模拟GitLab Webhook请求
def send_test_webhook(url, branch="main", token=None):
    """发送测试webhook请求到指定的URL"""
    try:
        # 构建测试数据
        test_data = {
            "event_name": "push",
            "user_name": "Test User",
            "ref": f"refs/heads/{branch}",
            "project_id": 12345,
            "project": {
                "name": "测试项目"
            },
            "commits": [
                {
                    "id": "abcdef1234567890abcdef1234567890abcdef12",
                    "author": {
                        "name": "Test User",
                        "email": "test@example.com"
                    },
                    "message": "测试代码提交\n\n这是一个测试提交，用于验证webhook功能是否正常工作。",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "added": ["src/new_file.py"],
                    "modified": ["src/main.py"],
                    "removed": ["src/old_file.py"]
                }
            ],
            "total_commits_count": 1
        }
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json",
            "X-Gitlab-Token": token if token else ""
        }
        
        # 发送请求
        logger.info(f"向 {url} 发送测试webhook请求，分支: {branch}")
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(test_data)
        )
        
        # 打印响应
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        
        return response.status_code
        
    except Exception as e:
        logger.error(f"发送测试webhook请求失败: {str(e)}")
        return None

# 主函数
def main():
    """主函数"""
    # 默认参数
    default_url = "http://localhost:8000/webhook/gitlab"
    default_branch = "main"
    default_token = "your-webhook-token"
    
    # 解析命令行参数
    url = default_url
    branch = default_branch
    token = default_token
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    if len(sys.argv) > 2:
        branch = sys.argv[2]
    if len(sys.argv) > 3:
        token = sys.argv[3]
    
    # 打印参数信息
    logger.info(f"使用参数:")
    logger.info(f"  URL: {url}")
    logger.info(f"  分支: {branch}")
    logger.info(f"  Token: {'已设置' if token else '未设置'}")
    
    # 发送测试请求
    status_code = send_test_webhook(url, branch, token)
    
    # 检查结果
    if status_code == 200:
        logger.info("测试webhook请求发送成功，webhook接收器工作正常！")
    elif status_code is not None:
        logger.warning(f"测试webhook请求发送失败，状态码: {status_code}")
    else:
        logger.error("测试webhook请求发送失败")

if __name__ == "__main__":
    main()