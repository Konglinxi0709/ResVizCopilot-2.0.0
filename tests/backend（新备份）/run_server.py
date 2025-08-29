"""
ResVizCopilot 2.0 后端服务启动脚本
"""
import uvicorn
from backend.config import settings
from backend.utils.logger import logger

if __name__ == "__main__":
    logger.info("启动ResVizCopilot 2.0后端服务")
    logger.info(f"配置信息:")
    logger.info(f"  - 服务地址: {settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    logger.info(f"  - DeepSeek模型: {settings.DEEPSEEK_REASONER_MODEL}, {settings.DEEPSEEK_V3_MODEL}")
    logger.info(f"  - 日志级别: {settings.LOG_LEVEL}")
    
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
