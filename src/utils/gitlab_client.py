import os
import logging
import requests
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)

class GitLabClient:
    """GitLab API客户端
    
    用于访问GitLab API，获取仓库文件内容等操作
    """
    def __init__(self, api_url: str, token: str):
        """初始化GitLab API客户端
        
        Args:
            api_url: GitLab API URL，例如：https://gitlab.example.com/api/v4
            token: GitLab访问令牌
        """
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.headers = {
            'Private-Token': self.token,
            'Content-Type': 'application/json'
        }
    
    def get_file_content(self, project_id: int, file_path: str, ref: str = 'main') -> Optional[str]:
        """获取GitLab仓库中指定文件的内容
        
        Args:
            project_id: GitLab项目ID
            file_path: 文件路径
            ref: Git分支或标签名，默认为'main'
        
        Returns:
            str: 文件内容，如果获取失败则返回None
        """
        try:
            url = f"{self.api_url}/projects/{project_id}/repository/files/{file_path.replace('/', '%2F')}/raw"
            params = {'ref': ref}
            
            logger.debug(f"获取GitLab文件内容: project_id={project_id}, file_path={file_path}, ref={ref}")
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"获取GitLab文件内容失败: status_code={response.status_code}, error={response.text}")
                return None
        except Exception as e:
            logger.error(f"获取GitLab文件内容时发生异常: {str(e)}")
            return None
    
    def list_repository_tree(self, project_id: int, path: str = '', ref: str = 'main', recursive: bool = False) -> Optional[List[Dict]]:
        """列出仓库目录结构
        
        Args:
            project_id: GitLab项目ID
            path: 目录路径，默认为空（根目录）
            ref: Git分支或标签名，默认为'main'
            recursive: 是否递归列出所有子目录
        
        Returns:
            List[Dict]: 目录结构列表，如果获取失败则返回None
        """
        try:
            url = f"{self.api_url}/projects/{project_id}/repository/tree"
            params = {
                'path': path,
                'ref': ref,
                'recursive': 1 if recursive else 0
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"列出GitLab目录结构失败: status_code={response.status_code}, error={response.text}")
                return None
        except Exception as e:
            logger.error(f"列出GitLab目录结构时发生异常: {str(e)}")
            return None
    
    def get_commit_diff(self, project_id: int, commit_id: str) -> Optional[Dict]:
        """获取提交的差异信息
        
        Args:
            project_id: GitLab项目ID
            commit_id: 提交ID
        
        Returns:
            Dict: 提交差异信息，如果获取失败则返回None
        """
        try:
            url = f"{self.api_url}/projects/{project_id}/repository/commits/{commit_id}/diff"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取GitLab提交差异失败: status_code={response.status_code}, error={response.text}")
                return None
        except Exception as e:
            logger.error(f"获取GitLab提交差异时发生异常: {str(e)}")
            return None

    def is_valid(self) -> bool:
        """验证GitLab客户端配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 尝试访问一个不需要特定权限的API端点来验证配置
            url = f"{self.api_url}/user"
            response = requests.get(url, headers=self.headers)
            return response.status_code == 200
        except:
            return False


def create_gitlab_client(api_url: Optional[str] = None, token: Optional[str] = None) -> Optional[GitLabClient]:
    """创建GitLab客户端实例
    
    如果未提供api_url和token，则尝试从环境变量或配置中获取
    
    Returns:
        GitLabClient: GitLab客户端实例，如果配置无效则返回None
    """
    from src.config import get_config
    
    # 优先级：参数 > 环境变量 > 配置文件
    if not api_url:
        api_url = os.environ.get("GITLAB_API_URL") or get_config("gitlab.api_url")
    
    if not token:
        token = os.environ.get("GITLAB_TOKEN") or get_config("gitlab.token")
    
    if not api_url or not token:
        logger.warning("GitLab API URL或Token未配置，无法创建GitLab客户端")
        return None
    
    client = GitLabClient(api_url, token)
    
    # 验证客户端配置是否有效
    if not client.is_valid():
        logger.error("GitLab客户端配置无效，请检查API URL和Token是否正确")
        return None
    
    logger.info("GitLab客户端创建成功")
    return client