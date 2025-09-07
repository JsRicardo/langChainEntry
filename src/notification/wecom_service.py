import requests
import json
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WeComNotificationService:
    """企业微信通知服务"""
    
    def __init__(self, webhook_url: str):
        """初始化企业微信通知服务
        
        Args:
            webhook_url: 企业微信机器人Webhook URL
        """
        if not webhook_url:
            raise ValueError("企业微信Webhook URL不能为空")
        self.webhook_url = webhook_url
        
    def send_markdown_notification(self, markdown_content: str, mentioned_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """发送Markdown格式的企业微信通知
        
        Args:
            markdown_content: Markdown格式的通知内容
            mentioned_list: 需要@的用户列表，默认为空
            
        Returns:
            微信机器人响应结果
        
        Raises:
            requests.exceptions.RequestException: 发送请求失败时抛出
        """
        try:
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": markdown_content,
                    "mentioned_list": mentioned_list or []
                }
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.webhook_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10  # 设置10秒超时
            )
            
            response.raise_for_status()
            logger.info(f"企业微信通知发送成功: {response.text}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"企业微信通知发送失败: {str(e)}")
            raise
    
    def send_text_notification(self, text: str, mentioned_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """发送文本格式的企业微信通知
        
        Args:
            text: 文本内容
            mentioned_list: 需要@的用户列表，默认为空
            
        Returns:
            微信机器人响应结果
        """
        try:
            payload = {
                "msgtype": "text",
                "text": {
                    "content": text,
                    "mentioned_list": mentioned_list or []
                }
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.webhook_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            response.raise_for_status()
            logger.info(f"企业微信文本通知发送成功: {response.text}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"企业微信文本通知发送失败: {str(e)}")
            raise
    
    def create_code_change_report(self, commit_info: Dict[str, Any], file_changes: List[Dict[str, Any]], 
                                impact_analysis: Dict[str, Any], test_suggestions: List[str], 
                                links: Dict[str, str]) -> str:
        """创建代码变更影响分析报告
        
        Args:
            commit_info: 提交信息
            file_changes: 文件变更列表
            impact_analysis: 影响分析结果
            test_suggestions: 测试建议列表
            links: 相关链接
            
        Returns:
            Markdown格式的报告内容
        """
        # 构建提交信息部分
        report = "# 代码变更影响分析报告\n\n"
        report += "## 变更基本信息\n"
        report += f"- **提交人**: {commit_info.get('author', '未知')}\n"
        report += f"- **提交时间**: {commit_info.get('time', '未知')}\n"
        report += f"- **分支**: {commit_info.get('branch', '未知')}\n"
        report += f"- **提交信息**: {commit_info.get('message', '无')}\n\n"
        
        # 构建文件变更部分
        report += "## 变更文件列表\n"
        for file in file_changes:
            file_path = file.get('path', '未知文件')
            change_type = file.get('type', '修改')
            report += f"- `{file_path}` ({change_type})\n"
        report += "\n"
        
        # 构建影响范围分析部分
        report += "## 影响范围分析\n"
        report += "### 前端影响\n"
        affected_pages = impact_analysis.get('affected_pages', [])
        if affected_pages:
            pages_str = "、".join(affected_pages)
            report += f"- **受影响页面**: {pages_str}\n"
        else:
            report += "- **受影响页面**: 无明确页面影响\n"
            
        affected_components = impact_analysis.get('affected_components', [])
        if affected_components:
            components_str = "、".join(affected_components)
            report += f"- **受影响组件**: {components_str}\n"
        else:
            report += "- **受影响组件**: 无明确组件影响\n"
            
        impact_score = impact_analysis.get('impact_score', 0)
        impact_level = "低" if impact_score < 30 else "中" if impact_score < 70 else "高"
        report += f"- **影响程度**: {impact_level}\n\n"
        
        # 构建潜在风险点部分
        risk_points = impact_analysis.get('risk_points', [])
        if risk_points:
            report += "### 潜在风险点\n"
            for risk in risk_points:
                report += f"- {risk}\n"
            report += "\n"
        
        # 构建测试建议部分
        if test_suggestions:
            report += "## 测试建议\n"
            for i, suggestion in enumerate(test_suggestions, 1):
                report += f"{i}. {suggestion}\n"
            report += "\n"
        
        # 构建关联信息部分
        if links:
            report += "## 关联信息\n"
            for link_text, link_url in links.items():
                report += f"- [{link_text}]({link_url})\n"
        
        return report

# 通知服务工厂函数
def create_wecom_notification_service(config_manager):
    """创建企业微信通知服务实例
    
    Args:
        config_manager: 配置管理器实例
        
    Returns:
        WeComNotificationService实例
    """
    webhook_url = config_manager.get("notification.wecom.webhook_url")
    return WeComNotificationService(webhook_url)