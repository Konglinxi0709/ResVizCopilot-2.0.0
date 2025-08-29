"""
模拟LLM客户端
支持流式输出模拟、错误模拟和延迟配置
"""
import asyncio
import random
from typing import List, AsyncGenerator

from utils.logger import logger


class NetworkError(Exception):
    """网络错误"""
    pass


class TimeoutError(Exception):
    """超时错误"""
    pass


class APIError(Exception):
    """API错误"""
    pass


class MockLLMClient:
    """
    模拟LLM客户端
    
    功能：
    1. 模拟流式输出，支持思考和内容分离
    2. 可配置延迟和错误模拟
    3. 支持不同类型的错误触发
    """
    
    def __init__(self):
        """初始化模拟客户端"""
        # 模拟响应内容
        self.mock_responses = [
            {
                "thinking": [
                    "让我思考一下这个问题...",
                    "需要考虑几个方面：",
                    "1. 首先分析问题的本质",
                    "2. 然后考虑可能的解决方案",
                    "3. 最后选择最佳方案"
                ],
                "content": [
                    "根据你的问题，我认为可以从以下几个角度来分析：\n\n",
                    "首先，我们需要明确问题的核心所在。",
                    "这样可以帮助我们找到最合适的解决方案。\n\n",
                    "其次，我建议采用循序渐进的方法，",
                    "这样可以确保每一步都是稳固的。\n\n",
                    "最后，我们需要持续监控和调整，",
                    "以确保方案能够达到预期效果。"
                ],
                "action": {
                    "title": "create_research_problem",
                    "params": {
                        "title": "新研究问题",
                        "significance": "这是一个重要的研究方向",
                        "criteria": "需要满足可行性和创新性要求"
                    }
                }
            }
        ]
        
        # 配置参数
        self.delay_per_token: float = 0.05  # 每个token的延迟
        self.error_rate: float = 0.0  # 错误概率
        self.error_types: List[str] = ["network", "timeout", "api_error"]
        
        logger.info("模拟LLM客户端初始化完成")
    
    def set_delay(self, delay_per_token: float) -> None:
        """设置响应延迟"""
        self.delay_per_token = delay_per_token
        logger.info(f"设置延迟: {delay_per_token}秒/token")
    
    def simulate_error(self, error_rate: float, error_types: List[str]) -> None:
        """
        配置错误模拟
        
        Args:
            error_rate: 错误概率 (0.0-1.0)
            error_types: 错误类型列表
        """
        self.error_rate = error_rate
        self.error_types = error_types
        logger.info(f"配置错误模拟: 概率={error_rate}, 类型={error_types}")
    
    def _maybe_raise_error(self) -> None:
        """根据配置可能抛出错误"""
        if random.random() < self.error_rate:
            error_type = random.choice(self.error_types)
            if error_type == "network":
                raise NetworkError("模拟网络连接错误")
            elif error_type == "timeout":
                raise TimeoutError("模拟请求超时")
            elif error_type == "api_error":
                raise APIError("模拟API调用错误")
    
    async def stream_generate(self, prompt: str) -> AsyncGenerator[dict, None]:
        """
        流式生成响应
        
        Args:
            prompt: 输入提示词
            
        Yields:
            包含thinking_content或content的字典
            
        Raises:
            NetworkError: 网络错误
            TimeoutError: 超时错误
            APIError: API错误
        """
        logger.info(f"开始流式生成，提示词长度: {len(prompt)}")
        
        # 选择一个模拟响应
        response = random.choice(self.mock_responses)
        
        # 流式输出思考过程
        logger.debug("开始输出思考过程")
        for thinking_chunk in response["thinking"]:
            # 检查是否要抛出错误
            self._maybe_raise_error()
            
            yield {"thinking_content": thinking_chunk + "\n"}
            await asyncio.sleep(self.delay_per_token * len(thinking_chunk))
        
        # 标记思考结束
        yield {"thinking_finished": True}
        await asyncio.sleep(self.delay_per_token * 2)
        
        # 流式输出内容
        logger.debug("开始输出主要内容")
        for content_chunk in response["content"]:
            # 检查是否要抛出错误
            self._maybe_raise_error()
            
            yield {"content": content_chunk}
            await asyncio.sleep(self.delay_per_token * len(content_chunk))
        
        # 输出行动指令（如果有）
        if "action" in response:
            logger.debug("输出行动指令")
            self._maybe_raise_error()
            
            yield {
                "action": response["action"]
            }
            await asyncio.sleep(self.delay_per_token * 5)
        
        # 标记生成完成
        yield {"finished": True}
        logger.info("流式生成完成")
    
    def get_stats(self) -> dict:
        """获取客户端统计信息"""
        return {
            "delay_per_token": self.delay_per_token,
            "error_rate": self.error_rate,
            "error_types": self.error_types,
            "available_responses": len(self.mock_responses)
        }
