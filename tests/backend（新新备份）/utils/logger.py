import logging
import sys
from datetime import datetime
from typing import Optional
import traceback


def setup_logger(name: str = "resviz_copilot", level: int = logging.INFO) -> logging.Logger:
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
    
    # 创建错误处理器（专门处理ERROR及以上级别的日志）
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 为错误处理器创建特殊格式化器，包含堆栈信息
    error_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s\n%(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    
    # 添加过滤器到错误处理器，使其只处理ERROR及以上级别的日志
    error_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    # 重写error和critical方法，自动添加异常信息
    def error_with_traceback(msg, *args, **kwargs):
        if logger.isEnabledFor(logging.ERROR):
            # 如果有异常信息，自动添加堆栈跟踪
            if 'exc_info' not in kwargs and sys.exc_info() != (None, None, None):
                kwargs['exc_info'] = True
            logger._log(logging.ERROR, msg, args, **kwargs)
    
    def critical_with_traceback(msg, *args, **kwargs):
        if logger.isEnabledFor(logging.CRITICAL):
            # 如果有异常信息，自动添加堆栈跟踪
            if 'exc_info' not in kwargs and sys.exc_info() != (None, None, None):
                kwargs['exc_info'] = True
            logger._log(logging.CRITICAL, msg, args, **kwargs)
    
    # 替换原始方法
    logger.error = error_with_traceback
    logger.critical = critical_with_traceback
    
    return logger


# 创建全局日志记录器实例
logger = setup_logger(level=logging.INFO)


def log_function_call(func_name: str, args: tuple = (), kwargs: Optional[dict] = None) -> None:
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


def log_multiline_text(text):
    """
    记录多行文本信息
    
    Args:
        text: 多行文本
    """
    lines = text.splitlines()  # 按行分割文本，自动处理不同换行符
    for line in lines:
        logger.info(line)  # 逐行打印