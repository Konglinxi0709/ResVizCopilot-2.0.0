"""
简单智能体实现
作为智能体抽象基类的示例派生类
"""
from typing import Dict, Any, List, Union
import asyncio

from core.agent_base import AgentBase
from core.simple_agent_prompts import PromptStrategy
from utils.logger import logger
from pydantic import BaseModel


class SimpleAgent(AgentBase):
    """
    简单智能体
    
    功能：
    1. 基本的对话处理
    2. 研究问题的创建和管理
    3. XML输出解析和行动执行
    """
    
    def __init__(self, *args, **kwargs):
        """初始化简单智能体"""
        super().__init__("SimpleAgent", *args, **kwargs)
        self._processed_requests = set()
        self.prompt_strategy = PromptStrategy()
        
        logger.info("简单智能体初始化完成")
    
    async def _agent_process(self, user_content: str) -> None:
        """
        智能体处理流程核心逻辑
        
        Args:
            user_content: 用户输入内容
        """
        while True:
            # 1. 判断当前处境
            should_continue = await self._assess_situation(user_content)
            if not should_continue:
                logger.info(f"简单智能体判断任务已完成")
                break
            
            # 2. 根据用户输入获取提示词和验证器
            prompt, validator = self.prompt_strategy.get_prompt_and_validator(user_content)
            
            # 3. 调用LLM（带可选验证）
            rollback_id = None  # 简单实现，不设置回溯点
            result = await self._call_llm_with_retry(
                prompt, 
                f"智能助手回复 (第{self.prompt_strategy.conversation_count}轮)",
                validator,
                rollback_id
            )
            
            # 4. 处理结果
            if isinstance(result, BaseModel):
                # 有验证器：结构化输出，执行行动
                await self._handle_structured_output(result)
            else:
                # 无验证器：纯文本输出，无需进一步处理
                logger.info("完成文本回复，无需执行行动")
            
            # 更新用户内容为空，进入下一轮循环判断
            user_content = ""
    
    async def _handle_structured_output(self, result: BaseModel) -> None:
        """
        处理结构化输出（有验证器的结果）
        
        Args:
            result: 验证后的结构化输出对象
        """
        try:
            # 提取行动类型和参数
            action_type = result.title
            action_params = result.params.model_dump()
            
            logger.info(f"执行结构化行动: {action_type}")
            
            # 执行行动
            await self._execute_action(action_type, action_params)
            
        except Exception as e:
            logger.error(f"处理结构化输出失败: {e}")
            raise
    
    async def _assess_situation(self, user_content: str) -> bool:
        """
        判断当前处境，决定是否需要继续处理
        
        Args:
            user_content: 用户输入内容
            
        Returns:
            是否需要继续处理
        """
        # 如果有新的用户输入，需要处理
        if user_content and user_content.strip():
            content_hash = hash(user_content.strip())
            if content_hash not in self._processed_requests:
                self._processed_requests.add(content_hash)
                logger.info(f"简单智能体判断: 需要处理新的用户请求")
                return True
            else:
                logger.info(f"简单智能体判断: 请求已处理过")
                return False
        
        # 简单的对话轮次限制（避免无限循环）
        if self.prompt_strategy.conversation_count >= 3:
            logger.info(f"简单智能体判断: 达到对话轮次限制，结束处理")
            return False
        
        # 其他情况下结束处理
        logger.info(f"简单智能体判断: 可以结束处理")
        return False
    

    
    def reset_conversation(self) -> None:
        """重置对话状态"""
        self.prompt_strategy.reset_conversation()
        self._processed_requests.clear()
        logger.info("简单智能体对话状态已重置")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        base_stats = super().get_stats()
        base_stats.update({
            "conversation_count": self.prompt_strategy.conversation_count,
            "processed_requests": len(self._processed_requests)
        })
        return base_stats