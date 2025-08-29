"""
日志工具模块
提供统一的日志记录功能
"""
import logging
import sys
from typing import Optional


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    设置并返回一个配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 创建控制台处理器
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper()))
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger


# 创建全局日志记录器
logger = setup_logger("stream_case")

