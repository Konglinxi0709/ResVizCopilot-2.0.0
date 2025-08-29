"""
模拟LLM客户端
使用回调函数发布patch，支持流式输出模拟、错误模拟和延迟配置
"""
import asyncio
import random
from typing import List, Callable, Dict, Any, Optional

from models.message import Patch
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
    
    优化功能：
    1. 使用回调函数发布patch而非yield方式
    2. 支持流式输出模拟，分离思考和内容
    3. 返回完整的content字符串
    4. 可配置延迟和错误模拟
    """
    
    def __init__(self, publish_callback: Optional[Callable] = None):
        """
        初始化模拟客户端
        
        Args:
            publish_callback: 发布patch的回调函数
        """
        self.publish_callback = publish_callback
        
        # 模拟响应内容 - 支持不同类型的输出
        self.response_templates = {
            # 普通聊天响应（无验证器）
            "chat": [
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
                    ]
                },
                {
                    "thinking": [
                        "这个问题很有意思...",
                        "我需要仔细考虑一下如何回答"
                    ],
                    "content": [
                        "感谢你提出这个问题。",
                        "让我为你详细解释一下。\n\n",
                        "基于我的理解，这个问题涉及到多个方面，",
                        "我会尽量给出全面而准确的回答。"
                    ]
                }
            ],
            
            # 创建研究问题响应（有验证器）
            "create_problem": [
                {
                    "thinking": [
                        "用户希望创建一个研究问题...",
                        "让我分析一下需求并设计合适的研究问题",
                        "需要确保研究问题具有实际价值"
                    ],
                    "content": [
                        "基于你的需求，我将为你创建一个研究问题。",
                        "这个问题具有重要的研究价值和实践意义。"
                    ],
                    "xml": '''<action>
<title>create_research_problem</title>
<params>
<title>智能体协程与流式传输解耦的技术方案研究</title>
<significance>该研究解决了智能体系统中协程独立性和实时传输的技术难题，对提升系统稳定性和用户体验具有重要意义。通过解耦技术可以实现更好的系统架构设计。</significance>
<criteria>需要满足协程独立运行、消息队列解耦、断连重连、错误重试等技术要求，同时保证系统的高可用性和可扩展性。</criteria>
</params>
</action>'''
                },
                {
                    "thinking": [
                        "分析用户的研究方向...",
                        "需要创建一个有价值的研究问题"
                    ],
                    "content": [
                        "我理解你的研究需求。",
                        "让我为你设计一个具有前瞻性的研究问题。"
                    ],
                    "xml": '''<action>
<title>create_research_problem</title>
<params>
<title>基于人工智能的自适应学习系统优化研究</title>
<significance>随着AI技术的发展，自适应学习系统在教育和培训领域具有巨大潜力，该研究有助于提升个性化学习效果和用户体验。</significance>
<criteria>研究需要涵盖算法设计、用户行为分析、系统性能评估等多个维度，并通过实验验证系统的有效性。</criteria>
</params>
</action>'''
                }
            ],
            
            # 查询问题响应（有验证器）
            "query_problems": [
                {
                    "thinking": [
                        "用户想要查询研究问题...",
                        "我需要构建合适的查询参数"
                    ],
                    "content": [
                        "我将为你搜索相关的研究问题。",
                        "让我根据你的需求设置查询条件。"
                    ],
                    "xml": '''<action>
<title>query_problems</title>
<params>
<keyword>人工智能</keyword>
<limit>10</limit>
</params>
</action>'''
                }
            ],
            
            # 更新问题响应（有验证器）
            "update_problem": [
                {
                    "thinking": [
                        "用户希望更新研究问题...",
                        "需要识别要更新的问题ID和新的内容"
                    ],
                    "content": [
                        "我将为你更新指定的研究问题。",
                        "让我根据你的要求进行修改。"
                    ],
                    "xml": '''<action>
<title>update_problem</title>
<params>
<id>problem-001</id>
<title>更新后的研究问题标题</title>
<significance>修订后的研究意义描述，体现了更深层次的研究价值。</significance>
<criteria>调整后的研究标准，包含了更具体的评估指标和成功标准。</criteria>
</params>
</action>'''
                }
            ]
        }
        
        # 配置参数
        self.delay_per_token: float = 0.05  # 每个token的延迟
        self.error_rate: float = 0.0  # 错误概率
        self.error_types: List[str] = ["network", "timeout", "api_error"]
        
        logger.info("模拟LLM客户端初始化完成")
    
    def set_publish_callback(self, callback: Callable) -> None:
        """设置发布回调函数"""
        self.publish_callback = callback
        logger.debug("设置发布回调函数")
    
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
    
    def _determine_response_type(self, prompt: str) -> str:
        """
        根据提示词内容确定响应类型
        
        Args:
            prompt: 提示词内容
            
        Returns:
            响应类型字符串
        """
        prompt_lower = prompt.lower()
        
        # 更精确的关键词匹配逻辑
        if ("create_research_problem" in prompt or 
            "创建研究问题" in prompt_lower or
            "创建" in prompt_lower and "研究问题" in prompt_lower or
            "新建" in prompt_lower and "问题" in prompt_lower or
            "建立" in prompt_lower and "研究" in prompt_lower):
            return "create_problem"
        elif ("query_problems" in prompt or 
              "查询问题" in prompt_lower or
              "搜索" in prompt_lower and "问题" in prompt_lower or
              "查找" in prompt_lower or
              "列出" in prompt_lower):
            return "query_problems"
        elif ("update_problem" in prompt or 
              "更新问题" in prompt_lower or
              "修改" in prompt_lower and "问题" in prompt_lower or
              "编辑" in prompt_lower):
            return "update_problem"
        else:
            return "chat"
    
    async def stream_generate(self, prompt: str, message_id: str) -> str:
        """
        流式生成响应
        
        Args:
            prompt: 输入提示词
            message_id: 消息ID
            
        Returns:
            完整的content字符串
            
        Raises:
            NetworkError: 网络错误
            TimeoutError: 超时错误
            APIError: API错误
        """
        if not self.publish_callback:
            raise ValueError("未设置发布回调函数")
        
        logger.info(f"开始流式生成，提示词长度: {len(prompt)}")
        
        # 根据提示词内容智能选择响应类型
        response_type = self._determine_response_type(prompt)
        responses = self.response_templates[response_type]
        response = random.choice(responses)
        
        full_content = ""
        
        try:
            # 流式输出思考过程
            logger.debug(f"开始输出思考过程 (类型: {response_type})")
            for thinking_chunk in response["thinking"]:
                # 检查是否要抛出错误
                self._maybe_raise_error()
                
                # 发布思考patch
                thinking_patch = Patch(
                    message_id=message_id,
                    thinking_delta=thinking_chunk + "\n"
                )
                await self.publish_callback(thinking_patch)
                
                await asyncio.sleep(self.delay_per_token * len(thinking_chunk))
            
            # 思考过程结束，短暂停顿
            await asyncio.sleep(self.delay_per_token * 2)
            
            # 流式输出内容
            logger.debug("开始输出主要内容")
            for content_chunk in response["content"]:
                # 检查是否要抛出错误
                self._maybe_raise_error()
                
                # 发布内容patch
                content_patch = Patch(
                    message_id=message_id,
                    content_delta=content_chunk
                )
                await self.publish_callback(content_patch)
                
                # 累积完整内容
                full_content += content_chunk
                
                await asyncio.sleep(self.delay_per_token * len(content_chunk))
            
            # 如果有XML行动，添加到输出中
            if "xml" in response:
                xml_content = response["xml"]
                
                # 流式输出XML（模拟真实场景）
                for i in range(0, len(xml_content), 50):  # 每50字符一块
                    chunk = xml_content[i:i+50]
                    
                    self._maybe_raise_error()
                    
                    content_patch = Patch(
                        message_id=message_id,
                        content_delta=chunk
                    )
                    await self.publish_callback(content_patch)
                    
                    full_content += chunk
                    await asyncio.sleep(self.delay_per_token * len(chunk))
            
            # 发布生成完成patch
            complete_patch = Patch(
                message_id=message_id,
                finished=True
            )
            await self.publish_callback(complete_patch)
            
            logger.info(f"流式生成完成 (类型: {response_type})")
            
            return full_content
            
        except (NetworkError, TimeoutError, APIError):
            # 重新抛出可重试的错误
            raise
        except Exception as e:
            logger.error(f"LLM生成过程出错: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        total_responses = sum(len(responses) for responses in self.response_templates.values())
        return {
            "delay_per_token": self.delay_per_token,
            "error_rate": self.error_rate,
            "error_types": self.error_types,
            "available_responses": total_responses,
            "response_types": list(self.response_templates.keys()),
            "has_callback": self.publish_callback is not None
        }

