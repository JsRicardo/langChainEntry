import sys
import os
import logging
import uvicorn

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import init_config, get_config
from src.api.webhook_receiver import app


# 配置日志
def setup_logging():
    """设置日志配置"""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            # 可选：添加文件日志
            # logging.FileHandler("app.log")
        ],
    )

    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


# 初始化应用
def initialize_app():
    """初始化应用"""
    # 初始化配置
    init_config()

    # 设置日志
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("代码变更分析系统初始化完成")


# 主函数
if __name__ == "__main__":
    # 初始化应用
    initialize_app()

    # 获取服务器配置
    host = get_config("server.host", "127.0.0.1")
    port = get_config("server.port", 8000)
    reload = get_config("server.reload", False)

    # 启动服务
    logger = logging.getLogger(__name__)
    logger.info(f"启动服务器，监听地址: http://{host}:{port}")

    # 使用导入的app对象启动服务
    uvicorn.run(app, host=host, port=port, reload=reload, log_level="info")

    # 从配置中读取服务设置
    host = get_config("server.host", "127.0.0.1")
    port = get_config("server.port", 3030)
    reload = get_config("server.reload", False)

    logger = logging.getLogger(__name__)
    logger.info(f"启动FastAPI服务，监听地址: http://{host}:{port}")

    # 启动UVicorn服务器
    uvicorn.run("src.main:app", host=host, port=port, reload=reload, log_level="info")
