import os
import yaml
import logging
from typing import Any, Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器，负责加载和管理系统配置"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config = {}
        # 加载环境变量
        load_dotenv()
    
    def load_config(self, config_path: str = "configs/config.json") -> None:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
        """
        # 尝试从不同位置加载配置文件
        possible_paths = [
            config_path,
            os.path.join(os.getcwd(), config_path),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", config_path)
        ]
        
        config_file_found = False
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.config = yaml.safe_load(f) or {}
                    logger.info(f"成功加载配置文件: {path}")
                    config_file_found = True
                    break
                except Exception as e:
                    logger.error(f"加载配置文件 {path} 失败: {str(e)}")
                    # 继续尝试其他路径
        
        if not config_file_found:
            logger.warning(f"未找到配置文件，使用默认配置")
        
        # 从环境变量覆盖配置
        self._override_with_env_vars()
    
    def _override_with_env_vars(self) -> None:
        """用环境变量覆盖配置"""
        # 企业微信配置
        wecom_webhook = os.environ.get("WECOM_WEBHOOK_URL")
        if wecom_webhook:
            if "notification" not in self.config:
                self.config["notification"] = {}
            if "wecom" not in self.config["notification"]:
                self.config["notification"]["wecom"] = {}
            self.config["notification"]["wecom"]["webhook_url"] = wecom_webhook
            logger.info("从环境变量覆盖企业微信Webhook配置")
            
        # AI配置
        ai_api_key = os.environ.get("AI_API_KEY")
        if ai_api_key:
            if "ai" not in self.config:
                self.config["ai"] = {}
            self.config["ai"]["api_key"] = ai_api_key
            logger.info("从环境变量覆盖AI API Key配置")
            
        # GitLab配置
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        if gitlab_token:
            if "gitlab" not in self.config:
                self.config["gitlab"] = {}
            self.config["gitlab"]["token"] = gitlab_token
            logger.info("从环境变量覆盖GitLab Token配置")
            
        gitlab_url = os.environ.get("GITLAB_API_URL")
        if gitlab_url:
            if "gitlab" not in self.config:
                self.config["gitlab"] = {}
            self.config["gitlab"]["api_url"] = gitlab_url
            logger.info("从环境变量覆盖GitLab API URL配置")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 "notification.wecom.webhook_url"
            default: 默认值，当配置不存在时返回
            
        Returns:
            配置值或默认值
        """
        keys = key.split(".")
        value = self.config
        
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except Exception as e:
            logger.error(f"获取配置 {key} 失败: {str(e)}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split(".")
        config = self.config
        
        for i, k in enumerate(keys[:-1]):
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置
        
        Returns:
            所有配置的字典
        """
        return self.config.copy()

# 全局配置管理器实例
global_config = ConfigManager()

# 初始化函数
def init_config(config_path: Optional[str] = None) -> None:
    """初始化配置管理器
    
    Args:
        config_path: 可选的配置文件路径
    """
    if config_path:
        global_config.load_config(config_path)
    else:
        global_config.load_config()

# 获取配置的便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """便捷获取配置值
    
    Args:
        key: 配置键
        default: 默认值
        
    Returns:
        配置值或默认值
    """
    return global_config.get(key, default)

# 设置配置的便捷函数
def set_config(key: str, value: Any) -> None:
    """便捷设置配置值
    
    Args:
        key: 配置键
        value: 配置值
    """
    global_config.set(key, value)