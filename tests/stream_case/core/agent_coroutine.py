"""
智能体协程
实现智能体的独立运行逻辑，包含LLM调用和行动处理
"""
import asyncio
from typing import AsyncGenerator

from models.message import Patch
from utils.logger import logger
from core.session_manager import SessionManager
from core.llm_client import MockLLMClient, NetworkError, TimeoutError, APIError
from core.action_handler import ActionHandler
from core.generator_retry import AgentGeneratorRetry


class AgentCoroutine:
    """
    智能体协程
    
    核心功能：
    1. 独立于SSE传输的协程运行
    2. 集成LLM调用、行动处理和重试机制
    3. 通过消息管道与传输层解耦
    """
    
    def __init__(self, session_mgr: SessionManager):
        """
        初始化智能体协程
        
        Args:
            session_mgr: 会话管理器
        """
        self.session_mgr = session_mgr
        self.llm_client = MockLLMClient()
        self.action_handler = ActionHandler()
        self.retry_wrapper = AgentGeneratorRetry()
        self._current_task: asyncio.Task = None
        
        logger.info("智能体协程初始化完成")
    
    async def process_user_message(self, content: str, title: str = "用户消息") -> None:
        """
        处理用户消息
        
        Args:
            content: 用户消息内容
            title: 消息标题
        """
        # 创建用户消息
        user_msg = self.session_mgr.create_message("user", title)
        user_msg.content = content
        user_msg.status = "completed"
        
        # 发布用户消息patch
        user_patch = Patch(
            message_id=user_msg.id,
            patch_type="complete",
            title=title,
            content_delta=content,
            finished=True
        )
        await self.session_mgr.publish_patch(user_patch)
        
        # 创建助手消息并启动生成过程
        assistant_msg = self.session_mgr.create_message("assistant", "智能体回复")
        
        # 发布新消息通知
        new_msg_patch = Patch(
            message_id=assistant_msg.id,
            patch_type="content",
            title="智能体回复",
            finished=False
        )
        await self.session_mgr.publish_patch(new_msg_patch)
        
        # 启动生成协程（使用重试包装器）
        self._current_task = asyncio.create_task(
            self._run_agent_generator(content, assistant_msg.id)
        )
        
        logger.info(f"开始处理用户消息: {content[:50]}...")
    
    async def _run_agent_generator(self, user_content: str, message_id: str) -> None:
        """
        运行智能体生成器（包含重试机制）
        
        Args:
            user_content: 用户输入内容
            message_id: 助手消息ID
        """
        try:
            async for patch in self.retry_wrapper.execute_with_retry(
                self._agent_generator,
                self.session_mgr,
                user_content,
                message_id
            ):
                await self.session_mgr.publish_patch(patch)
        except Exception as e:
            logger.error(f"智能体生成器执行失败: {e}")
        finally:
            self._current_task = None
    
    async def _agent_generator(self, user_content: str, message_id: str) -> AsyncGenerator[Patch, None]:
        """
        智能体生成器核心逻辑
        
        Args:
            user_content: 用户输入内容
            message_id: 助手消息ID
            
        Yields:
            Patch对象
        """
        logger.info("开始智能体生成器执行")
        
        try:
            # 调用LLM流式生成
            async for llm_output in self.llm_client.stream_generate(user_content):
                
                if "thinking_content" in llm_output:
                    # 思考过程
                    patch = Patch(
                        message_id=message_id,
                        patch_type="thinking",
                        thinking_delta=llm_output["thinking_content"],
                        finished=False
                    )
                    yield patch
                
                elif "thinking_finished" in llm_output:
                    # 思考过程结束
                    logger.debug("思考过程完成")
                
                elif "content" in llm_output:
                    # 主要内容
                    patch = Patch(
                        message_id=message_id,
                        patch_type="content",
                        content_delta=llm_output["content"],
                        finished=False
                    )
                    yield patch
                
                elif "action" in llm_output:
                    # 行动指令
                    action_data = llm_output["action"]
                    action = self.action_handler.parse_actions(action_data)
                    
                    if action:
                        # 执行行动
                        result = self.action_handler.execute_action(
                            action["title"], 
                            action["params"]
                        )
                        
                        # 发送行动结果patch
                        action_patch = Patch(
                            message_id=message_id,
                            patch_type="action",
                            action_title=action["title"],
                            action_params=action["params"],
                            content_delta=f"\n\n[行动执行] {result['message']}\n",
                            snapshot_id=result.get("snapshot_id", ""),
                            finished=False
                        )
                        yield action_patch
                
                elif "finished" in llm_output:
                    # 生成完成
                    complete_patch = Patch(
                        message_id=message_id,
                        patch_type="complete",
                        finished=True
                    )
                    yield complete_patch
                    logger.info("智能体生成完成")
                    break
        
        except (NetworkError, TimeoutError, APIError) as e:
            # 这些是可重试的错误，让重试包装器处理
            logger.warning(f"LLM调用出错（可重试）: {e}")
            raise
        
        except Exception as e:
            # 其他不可重试的错误
            logger.error(f"智能体生成器出错（不可重试）: {e}")
            raise
    
    async def stop_generation(self) -> bool:
        """
        停止当前生成任务
        
        Returns:
            是否成功停止
        """
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                logger.info("生成任务已取消")
                return True
            except Exception as e:
                logger.error(f"取消生成任务时出错: {e}")
                return False
        
        return False
    
    def is_generating(self) -> bool:
        """检查是否正在生成"""
        return self._current_task is not None and not self._current_task.done()
    
    def configure_llm(self, **kwargs) -> None:
        """
        配置LLM客户端
        
        Args:
            **kwargs: 配置参数
        """
        if "delay_per_token" in kwargs:
            self.llm_client.set_delay(kwargs["delay_per_token"])
        
        if "error_rate" in kwargs and "error_types" in kwargs:
            self.llm_client.simulate_error(
                kwargs["error_rate"], 
                kwargs["error_types"]
            )
        
        logger.info(f"LLM配置已更新: {kwargs}")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "is_generating": self.is_generating(),
            "llm_stats": self.llm_client.get_stats(),
            "retry_stats": self.retry_wrapper.get_retry_stats(),
            "database_state": self.action_handler.get_database_state()
        }
