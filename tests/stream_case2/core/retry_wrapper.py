"""
重试包装器
实现对智能体调用和数据库操作的错误重试机制，使用指数回退策略
"""
import asyncio
from typing import Callable, Any, Optional, Dict
import traceback

from models.message import Patch
from core.llm_client import NetworkError, TimeoutError as LLMTimeoutError, APIError
from utils.logger import logger


class RetryWrapper:
    """
    重试包装器
    
    功能：
    1. 对智能体调用和数据库操作实现重试机制
    2. 使用指数回退延迟算法
    3. 区分可重试和不可重试错误
    4. 通过回调函数发布重试状态
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        初始化重试包装器
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "total_delay": 0.0
        }
        
        logger.info(f"重试包装器初始化: 最大重试{max_retries}次")
    
    async def execute_with_retry(self,
                               func: Callable,
                               publish_callback: Callable,
                               rollback_message_id: Optional[str],
                               *args, **kwargs) -> Any:
        """
        执行函数并在失败时重试
        
        Args:
            func: 要执行的函数
            publish_callback: 发布patch的回调函数
            rollback_message_id: 重试失败时回溯到的消息ID
            *args, **kwargs: 传递给函数的参数
            
        Returns:
            函数执行结果
            
        Raises:
            Exception: 重试失败后抛出最后一次的异常
        """
        
        for attempt in range(self.max_retries + 1):
            self.retry_stats["total_attempts"] += 1
            
            try:
                logger.info(f"开始第{attempt + 1}次尝试 (共{self.max_retries + 1}次)")
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 成功完成
                self.retry_stats["successful_attempts"] += 1
                logger.info("函数执行成功完成")
                return result
                
            except Exception as e:
                # 检查是否为可重试的错误
                if self._should_retry(e):
                    logger.warning(f"第{attempt + 1}次尝试失败（可重试错误）: {e}")
                    
                    if attempt < self.max_retries:
                        # 回溯消息列表到重试前状态
                        if rollback_message_id:
                            await self._rollback_messages(publish_callback, rollback_message_id)
                        
                        # 计算延迟时间
                        delay = self._calculate_delay(attempt)
                        self.retry_stats["total_delay"] += delay
                        
                        # 发送重试通知patch
                        await self._send_retry_notification(
                            publish_callback, 
                            attempt + 1, 
                            delay, 
                            str(e)
                        )
                        
                        logger.info(f"等待{delay:.1f}秒后重试")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # 超过最大重试次数
                        self.retry_stats["failed_attempts"] += 1
                        await self._send_failure_notification(
                            publish_callback, 
                            str(e)
                        )
                        logger.error(f"重试{self.max_retries}次后仍然失败: {e}")
                        raise
                else:
                    # 不可重试的错误
                    self.retry_stats["failed_attempts"] += 1
                    await self._send_error_notification(
                        publish_callback, 
                        str(e)
                    )
                    logger.error(f"发生不可重试错误: {e}")
                    logger.debug(f"错误堆栈: {traceback.format_exc()}")
                    raise
    

    
    def _should_retry(self, exception: Exception) -> bool:
        """
        判断异常是否可重试
        
        Args:
            exception: 异常对象
            
        Returns:
            是否可重试
        """
        # 可重试的错误类型
        retryable_errors = (
            NetworkError,
            LLMTimeoutError,
            ConnectionError,
            OSError,
            TimeoutError,
            # 可以添加更多可重试的错误类型
        )
        
        return isinstance(exception, retryable_errors)
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        计算延迟时间（指数回退）
        
        Args:
            attempt: 当前尝试次数（从0开始）
            
        Returns:
            延迟时间（秒）
        """
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    async def _rollback_messages(self, publish_callback: Callable, rollback_message_id: str) -> None:
        """
        回溯消息列表到指定状态
        
        Args:
            publish_callback: 发布回调函数
            rollback_message_id: 回溯到的消息ID
        """
        try:
            # 发布回溯patch
            rollback_patch = Patch(
                message_id=rollback_message_id,
                rollback=True
            )
            await publish_callback(rollback_patch)
            logger.info(f"回溯消息状态到: {rollback_message_id}")
        except Exception as e:
            logger.error(f"回溯消息状态失败: {e}")
    
    async def _send_retry_notification(self,
                                     publish_callback: Callable,
                                     attempt: int,
                                     delay: float,
                                     error_msg: str) -> None:
        """发送重试通知"""
        try:
            retry_patch = Patch(
                message_id=None,  # 创建新消息
                title=f"重试通知 ({attempt}/{self.max_retries})",
                content_delta=f"检测到网络错误：{error_msg}\n正在{delay:.1f}秒后重试...\n",
                finished=True
            )
            
            await publish_callback(retry_patch)
        except Exception as e:
            logger.error(f"发送重试通知失败: {e}")
    
    async def _send_failure_notification(self,
                                       publish_callback: Callable,
                                       error_msg: str) -> None:
        """发送失败通知"""
        try:
            failure_patch = Patch(
                message_id=None,  # 创建新消息
                title="重试失败通知",
                content_delta=f"重试{self.max_retries}次后仍然失败：{error_msg}\n",
                finished=True
            )
            
            await publish_callback(failure_patch)
        except Exception as e:
            logger.error(f"发送失败通知失败: {e}")
    
    async def _send_error_notification(self,
                                     publish_callback: Callable,
                                     error_msg: str) -> None:
        """发送错误通知"""
        try:
            error_patch = Patch(
                message_id=None,  # 创建新消息
                title="错误通知",
                content_delta=f"发生不可重试错误：{error_msg}\n",
                finished=True
            )
            
            await publish_callback(error_patch)
        except Exception as e:
            logger.error(f"发送错误通知失败: {e}")
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """
        获取重试统计信息
        
        Returns:
            包含重试统计的字典
        """
        failed_attempts = self.retry_stats["total_attempts"] - self.retry_stats["successful_attempts"]
        avg_delay = (self.retry_stats["total_delay"] / max(1, failed_attempts))
        
        return {
            "total_attempts": self.retry_stats["total_attempts"],
            "successful_attempts": self.retry_stats["successful_attempts"],
            "failed_attempts": failed_attempts,
            "average_delay": avg_delay,
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.retry_stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "total_delay": 0.0
        }
        logger.info("重试统计信息已重置")

