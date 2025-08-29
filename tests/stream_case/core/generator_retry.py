"""
智能体生成器重试包装器
实现对整个生成过程的重试机制
"""
import asyncio
from typing import AsyncGenerator, Callable, Any
import traceback

from models.message import Patch
from utils.logger import logger


class AgentGeneratorRetry:
    """
    智能体生成器重试包装器
    
    根据原设计，错误重试机制应该包装整个智能体调用生成器，
    而不仅仅是单个API调用
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
                               generator_func: Callable,
                               session_mgr,
                               *args, **kwargs) -> AsyncGenerator[Patch, None]:
        """
        重试包装整个智能体生成器函数
        
        Args:
            generator_func: 智能体生成器函数
            session_mgr: 会话管理器
            *args, **kwargs: 传递给生成器函数的参数
            
        Yields:
            Patch对象
        """
        for attempt in range(self.max_retries + 1):
            self.retry_stats["total_attempts"] += 1
            
            try:
                # 记录重试前的消息状态，用于回溯
                snapshot_before_attempt = session_mgr.get_current_message_id()
                
                logger.info(f"开始第{attempt + 1}次尝试 (共{self.max_retries + 1}次)")
                
                # 执行整个生成器过程
                async for patch in generator_func(*args, **kwargs):
                    yield patch
                
                # 如果成功完成，直接返回
                self.retry_stats["successful_attempts"] += 1
                logger.info("生成器执行成功完成")
                return
                
            except Exception as e:
                # 检查是否为可重试的错误
                from core.llm_client import NetworkError, TimeoutError as LLMTimeoutError, APIError
                
                if isinstance(e, (NetworkError, LLMTimeoutError, ConnectionError, OSError)):
                    # 可重试的错误
                    logger.warning(f"第{attempt + 1}次尝试失败（可重试错误）: {e}")
                    
                    if attempt < self.max_retries:
                        # 回溯消息列表到重试前状态
                        await self._rollback_messages(session_mgr, snapshot_before_attempt)
                        
                        # 计算延迟时间
                        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                        self.retry_stats["total_delay"] += delay
                        
                        # 发送重试通知patch
                        retry_patch = Patch(
                            message_id=session_mgr.current_message_id,
                            patch_type="retry",
                            content_delta=f"\n[重试 {attempt+1}/{self.max_retries}] 检测到网络错误，{delay:.1f}秒后重试...\n",
                            finished=False
                        )
                        yield retry_patch
                        
                        logger.info(f"等待{delay:.1f}秒后重试")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # 超过最大重试次数，发送失败通知
                        self.retry_stats["failed_attempts"] += 1
                        error_patch = Patch(
                            message_id=session_mgr.current_message_id,
                            patch_type="error",
                            content_delta=f"\n[错误] 重试{self.max_retries}次后仍然失败: {str(e)}\n",
                            finished=True
                        )
                        yield error_patch
                        logger.error(f"重试{self.max_retries}次后仍然失败: {e}")
                        raise
                else:
                    # 不可重试的错误，直接抛出
                    self.retry_stats["failed_attempts"] += 1
                    error_patch = Patch(
                        message_id=session_mgr.current_message_id,
                        patch_type="error", 
                        content_delta=f"\n[错误] 发生不可重试错误: {str(e)}\n",
                        finished=True
                    )
                    yield error_patch
                    logger.error(f"发生不可重试错误: {e}")
                    logger.debug(f"错误堆栈: {traceback.format_exc()}")
                    raise
    
    async def _rollback_messages(self, session_mgr, snapshot_id: str) -> None:
        """
        回溯消息列表到指定状态
        
        Args:
            session_mgr: 会话管理器
            snapshot_id: 快照ID（这里是消息ID）
        """
        try:
            # 清除当前未完成的消息内容，准备重新生成
            if session_mgr.current_message_id:
                current_msg = session_mgr.get_message(session_mgr.current_message_id)
                if current_msg and current_msg.status == "generating":
                    # 清空thinking和content，保留消息框架
                    current_msg.thinking = ""
                    current_msg.content = ""
                    current_msg.action_title = ""
                    current_msg.action_params = {}
                    current_msg.snapshot_id = ""
                    current_msg.update_timestamp()
                    
                    logger.info(f"回溯消息状态: {current_msg.id}")
        except Exception as e:
            logger.error(f"回溯消息状态失败: {e}")
    
    def get_retry_stats(self) -> dict:
        """
        获取重试统计信息
        
        Returns:
            包含重试统计的字典
        """
        avg_delay = (self.retry_stats["total_delay"] / 
                    max(1, self.retry_stats["total_attempts"] - self.retry_stats["successful_attempts"]))
        
        return {
            "total_attempts": self.retry_stats["total_attempts"],
            "successful_attempts": self.retry_stats["successful_attempts"],
            "failed_attempts": self.retry_stats["failed_attempts"],
            "average_delay": avg_delay
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
