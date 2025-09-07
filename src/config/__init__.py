# 配置模块初始化文件

from .config_manager import ConfigManager, global_config, init_config, get_config, set_config

__all__ = [
    "ConfigManager",
    "global_config",
    "init_config",
    "get_config",
    "set_config"
]