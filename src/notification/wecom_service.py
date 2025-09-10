import json
import requests
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
            links: 相关链接字典
            
        Returns:
            str: Markdown格式的报告内容
        """
        # 构建报告头部
        report = []
        report.append("# 代码变更分析报告")
        report.append("")
        
        # 提交信息部分
        report.append("## 提交信息")
        report.append(f"- **提交人**: {commit_info.get('author', '未知')}")
        report.append(f"- **提交时间**: {commit_info.get('timestamp', '未知')}")
        report.append(f"- **提交信息**: {commit_info.get('message', '无')}")
        report.append(f"- **分支**: {commit_info.get('branch', '未知')}")
        report.append("")
        
        # 文件变更部分
        report.append("## 文件变更")
        if file_changes:
            for file in file_changes[:5]:  # 只显示前5个文件，避免信息过多
                status = file.get('status', 'unknown')
                filename = file.get('path', '未知文件')
                report.append(f"- {status.upper()}: `{filename}`")
            if len(file_changes) > 5:
                report.append(f"- 还有 {len(file_changes) - 5} 个文件变更，详见GitLab")
        else:
            report.append("- 暂无文件变更")
        report.append("")
        
        # 影响分析部分
        report.append("## 影响分析")
        if impact_analysis:
            # 风险等级
            risk_level = impact_analysis.get('risk_level', '未知')
            risk_emoji = "⚠️" if risk_level in ['高', 'medium', 'high'] else "✅" if risk_level == '低' else "​"
            report.append(f"- **风险等级**: {risk_emoji} {risk_level}")
            
            # 模块影响
            module_impact = impact_analysis.get('module_impact', [])
            if module_impact:
                report.append("- **影响模块**: " + ", ".join(module_impact))
            
            # 接口影响
            interface_impact = impact_analysis.get('interface_impact', [])
            if interface_impact:
                report.append("- **影响接口**: " + ", ".join(interface_impact))
            
            # 业务影响
            business_impact = impact_analysis.get('business_impact', '')
            if business_impact:
                report.append(f"- **业务影响**: {business_impact}")
        else:
            report.append("- 暂无影响分析结果")
        report.append("")
        
        # 测试建议部分
        report.append("## 测试建议")
        if test_suggestions:
            for suggestion in test_suggestions:
                report.append(f"- {suggestion}")
        else:
            report.append("- 暂无测试建议")
        report.append("")
        
        # 相关链接部分
        report.append("## 相关链接")
        if links:
            for link_name, link_url in links.items():
                report.append(f"- [{link_name}]({link_url})")
        report.append("")
        
        # 添加生成时间
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report.append(f"*报告生成时间: {current_time}*")
        
        return "\n".join(report)


def create_wecom_notification_service() -> WeComNotificationService:
    """创建企业微信通知服务实例的工厂函数
    
    Returns:
        WeComNotificationService: 企业微信通知服务实例
    """
    try:
        from src.config.config_manager import get_config, init_config
        
        # 初始化配置
        init_config()
        
        # 获取企业微信Webhook URL配置
        webhook_url = get_config("notification.wecom.webhook_url")
        
        if not webhook_url:
            # 如果配置中没有，尝试从环境变量获取
            import os
            webhook_url = os.environ.get("WECOM_WEBHOOK_URL")
            
            if not webhook_url:
                logger.warning("企业微信Webhook URL未配置，使用模拟服务")
                # 创建一个模拟的服务实例，用于开发和测试环境
                return MockWeComNotificationService()
        
        logger.info("创建企业微信通知服务实例")
        return WeComNotificationService(webhook_url)
    except Exception as e:
        logger.error(f"创建企业微信通知服务实例失败: {str(e)}")
        # 返回模拟服务，确保系统可以继续运行
        return MockWeComNotificationService()


class MockWeComNotificationService:
    """模拟的企业微信通知服务，用于开发和测试环境"""
    
    def __init__(self):
        logger.info("使用模拟企业微信通知服务")
        
    def send_markdown_notification(self, markdown_content: str, mentioned_list: Optional[List[str]] = None) -> Dict[str, Any]:
        logger.info(f"模拟发送Markdown通知:\n{markdown_content}\n@用户: {mentioned_list or []}")
        return {"errcode": 0, "errmsg": "ok"}
    
    def send_text_notification(self, text: str, mentioned_list: Optional[List[str]] = None) -> Dict[str, Any]:
        logger.info(f"模拟发送文本通知:\n{text}\n@用户: {mentioned_list or []}")
        return {"errcode": 0, "errmsg": "ok"}
    
    def create_code_change_report(self, commit_info: Dict[str, Any], file_changes: List[Dict[str, Any]], 
                                impact_analysis: Dict[str, Any], test_suggestions: List[str], 
                                links: Dict[str, str]) -> str:
        # 调用真实服务的方法来生成报告
        dummy_service = WeComNotificationService("dummy-url")
        return dummy_service.create_code_change_report(
            commit_info, file_changes, impact_analysis, test_suggestions, links
        )