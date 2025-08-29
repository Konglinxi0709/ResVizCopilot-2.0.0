"""
日志工具模块
提供统一的日志记录功能
"""
import logging
import sys
from datetime import datetime


def setup_logger(name: str = "stream_case2", level: int = logging.INFO) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    return logger


# 创建全局日志记录器实例
logger = setup_logger()


def log_function_call(func_name: str, args: tuple = (), kwargs: dict = None) -> None:
    """
    记录函数调用信息
    
    Args:
        func_name: 函数名称
        args: 位置参数
        kwargs: 关键字参数
    """
    kwargs = kwargs or {}
    args_str = ", ".join([str(arg) for arg in args])
    kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    
    all_args = []
    if args_str:
        all_args.append(args_str)
    if kwargs_str:
        all_args.append(kwargs_str)
    
    params_str = ", ".join(all_args)
    logger.debug(f"调用函数: {func_name}({params_str})")


def log_performance(operation: str, start_time: datetime, end_time: datetime) -> None:
    """
    记录性能信息
    
    Args:
        operation: 操作名称
        start_time: 开始时间
        end_time: 结束时间
    """
    duration = (end_time - start_time).total_seconds()
    logger.info(f"性能统计: {operation} 耗时 {duration:.3f}秒")

