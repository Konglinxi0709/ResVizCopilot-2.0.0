"""
DeepSeek LLM客户端
支持推理模型(reasoner)和普通模型(v3)的流式生成
"""
import asyncio
from typing import Optional, Callable, Dict, Any, List
from openai import AsyncOpenAI

from backend.config import settings
from backend.utils.logger import logger, log_multiline_text
from backend.agents.retry_wrapper import NetworkError, TimeoutError, APIError
from backend.message.schemas.message_models import Patch

class DeepSeekClient:
    """
    DeepSeek LLM客户端
    
    功能：
    1. 支持reasoner模型（带思考过程）和v3模型（仅内容）
    2. 流式生成，实时发布patch更新
    3. 错误处理和统计信息
    """
    
    def __init__(self, 
                 model_type: str = "reasoner",
                 publish_callback: Optional[Callable] = None):
        """
        初始化DeepSeek客户端
        
        Args:
            model_type: 模型类型，"reasoner" 或 "v3"
            publish_callback: 发布patch的回调函数
        """
        self.model_type = model_type
        self.publish_callback = publish_callback
        
        # 根据模型类型选择模型
        if model_type == "reasoner":
            self.model_name = settings.DEEPSEEK_REASONER_MODEL
            self.supports_reasoning = True
        else:  # v3
            self.model_name = settings.DEEPSEEK_V3_MODEL
            self.supports_reasoning = False
        
        # 初始化OpenAI客户端
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        
        # 统计信息
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_thinking_tokens": 0,
            "total_content_tokens": 0,
            "total_time": 0.0
        }
        
        logger.info(f"DeepSeek客户端初始化完成 - 模型: {self.model_name}, 支持推理: {self.supports_reasoning}")
    
    def set_publish_callback(self, callback: Callable) -> None:
        """设置发布回调函数"""
        self.publish_callback = callback
    
    async def stream_generate(self, 
                            prompt: str, 
                            message_id: str,
                            max_tokens: int = None,
                            temperature: float = None,
                            publish_content: bool = True) -> str:
        """
        流式生成响应
        
        Args:
            prompt: 提示词
            message_id: 消息ID
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            完整的生成内容
            
        Raises:
            NetworkError, TimeoutError, APIError: 各种错误
        """
        import time
        start_time = time.time()
        
        self.stats["total_calls"] += 1
        
        try:
            # 设置默认参数
            max_tokens = max_tokens or settings.DEFAULT_MAX_TOKENS
            temperature = temperature or settings.DEFAULT_TEMPERATURE
            
            # 构建消息
            messages = [{"role": "user", "content": prompt}]
            
            logger.info(f"开始调用{self.model_type}模型生成 - 消息ID: {message_id}")
            logger.info("【提示词内容】:")
            log_multiline_text(prompt)
            # 调用DeepSeek API
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 处理流式响应
            full_content = await self._process_stream_response(response, message_id, publish_content)
            
            # 更新统计
            self.stats["successful_calls"] += 1
            self.stats["total_time"] += time.time() - start_time
            logger.info(f"模型生成完成 - 消息ID: {message_id}, 内容长度: {len(full_content)}")
            return full_content
            
        except Exception as e:
            self.stats["failed_calls"] += 1
            logger.error(f"模型生成失败 - 消息ID: {message_id}, 错误: {e}")
            
            # 转换为标准错误类型
            if "timeout" in str(e).lower():
                raise TimeoutError(f"DeepSeek API超时: {e}")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise NetworkError(f"DeepSeek API网络错误: {e}")
            else:
                raise APIError(f"DeepSeek API错误: {e}")
    
    async def _process_stream_response(self, response, message_id: str, publish_content: bool) -> str:
        """
        处理流式响应
        
        Args:
            response: 流式响应对象
            message_id: 消息ID
            
        Returns:
            完整内容
        """
        full_content = ""
        full_thinking = ""
        reasoning_phase = True  # 是否在推理阶段
        
        try:
            async for chunk in response:
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                
                # 处理推理内容（仅reasoner模型）
                if self.supports_reasoning and delta.reasoning_content:
                    reasoning_content = delta.reasoning_content
                    full_thinking += reasoning_content
                    self.stats["total_thinking_tokens"] += len(reasoning_content.split())
                    
                    # 发布思考增量patch
                    if self.publish_callback:
                        thinking_patch = Patch(
                            message_id=message_id,
                            thinking_delta=reasoning_content
                        )
                        await self.publish_callback(thinking_patch)
                
                # 处理普通内容
                elif delta.content:
                    if reasoning_phase:
                        # 思考阶段结束，进入内容阶段
                        reasoning_phase = False
                        logger.info("【思考内容】:")
                        log_multiline_text(full_thinking)
                        logger.debug(f"思考阶段结束，开始生成内容 - 消息ID: {message_id}")
                    
                    content = delta.content
                    full_content += content
                    self.stats["total_content_tokens"] += len(content.split())
                    
                    # 发布内容增量patch
                    if self.publish_callback and publish_content:
                        content_patch = Patch(
                            message_id=message_id,
                            content_delta=content
                        )
                        await self.publish_callback(content_patch)
            
            # 发布完成patch
            if self.publish_callback:
                finish_patch = Patch(
                    message_id=message_id,
                    finished=True
                )
                await self.publish_callback(finish_patch)
            
            # 更新总token统计
            self.stats["total_tokens"] += len(full_content.split()) + len(full_thinking.split())
            logger.info("【输出内容】:")
            log_multiline_text(full_content)
            logger.debug(f"流式处理完成 - 消息ID: {message_id}, 思考长度: {len(full_thinking)}, 内容长度: {len(full_content)}")
            return full_content
            
        except Exception as e:
            logger.error(f"处理流式响应失败 - 消息ID: {message_id}, 错误: {e}")
            raise APIError(f"处理流式响应失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            包含各种统计数据的字典
        """
        success_rate = 0.0
        if self.stats["total_calls"] > 0:
            success_rate = self.stats["successful_calls"] / self.stats["total_calls"]
        
        avg_time = 0.0
        if self.stats["successful_calls"] > 0:
            avg_time = self.stats["total_time"] / self.stats["successful_calls"]
        
        return {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "supports_reasoning": self.supports_reasoning,
            "total_calls": self.stats["total_calls"],
            "successful_calls": self.stats["successful_calls"],
            "failed_calls": self.stats["failed_calls"],
            "success_rate": success_rate,
            "total_tokens": self.stats["total_tokens"],
            "total_thinking_tokens": self.stats["total_thinking_tokens"],
            "total_content_tokens": self.stats["total_content_tokens"],
            "average_time_per_call": avg_time
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_thinking_tokens": 0,
            "total_content_tokens": 0,
            "total_time": 0.0
        }
        logger.info(f"重置{self.model_type}模型统计信息")


class DeepSeekReasonerClient(DeepSeekClient):
    """DeepSeek推理模型客户端（带思考过程）"""
    
    def __init__(self, publish_callback: Optional[Callable] = None):
        super().__init__(model_type="reasoner", publish_callback=publish_callback)


class DeepSeekV3Client(DeepSeekClient):
    """DeepSeek V3模型客户端（仅内容，无思考过程）"""
    
    def __init__(self, publish_callback: Optional[Callable] = None):
        super().__init__(model_type="v3", publish_callback=publish_callback)
