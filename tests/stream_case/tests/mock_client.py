"""
模拟客户端
用于测试SSE连接和消息流程
"""
import asyncio
import json
import time
import sys
import os
from typing import AsyncGenerator, Dict, Any

import httpx

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger


class MockSSEClient:
    """
    模拟SSE客户端
    支持连接、断连、重连测试
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        初始化模拟客户端
        
        Args:
            base_url: 服务器基础URL
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.connected_sessions = {}
        
        logger.info(f"模拟客户端初始化: {base_url}")
    
    async def send_message(self, content: str, title: str = "测试消息") -> AsyncGenerator[Dict[str, Any], None]:
        """
        发送消息并接收SSE流
        
        Args:
            content: 消息内容
            title: 消息标题
            
        Yields:
            SSE事件字典
        """
        logger.info(f"发送消息: {content[:50]}...")
        
        # 构建请求
        params = {
            "content": content,
            "title": title
        }
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/agents/messages",
                json=params,
                headers={"Accept": "text/event-stream"}
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"请求失败: {response.status_code}")
                    return
                
                logger.info("SSE连接建立成功")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # 移除"data: "前缀
                            yield {
                                "event": "patch",
                                "data": data,
                                "timestamp": time.time()
                            }
                            
                            # 如果消息完成，结束接收
                            if data.get("finished", False):
                                logger.info("消息接收完成")
                                break
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析SSE数据失败: {e}")
                    
                    elif line.startswith("event: "):
                        event_type = line[7:]
                        logger.debug(f"收到事件类型: {event_type}")
        
        except Exception as e:
            logger.error(f"SSE连接错误: {e}")
            raise
    
    async def get_message_history(self) -> Dict[str, Any]:
        """获取消息历史"""
        try:
            response = await self.client.get(f"{self.base_url}/agents/messages/history")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取消息历史失败: {e}")
            raise
    
    async def continue_message(self, message_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        继续接收未完成的消息
        
        Args:
            message_id: 消息ID
            
        Yields:
            SSE事件字典
        """
        logger.info(f"继续接收消息: {message_id}")
        
        try:
            async with self.client.stream(
                "GET",
                f"{self.base_url}/agents/messages/continue/{message_id}",
                headers={"Accept": "text/event-stream"}
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"继续消息失败: {response.status_code}")
                    return
                
                logger.info("重连SSE成功")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            yield {
                                "event": "continue",
                                "data": data,
                                "timestamp": time.time()
                            }
                            
                            if data.get("finished", False):
                                logger.info("继续消息完成")
                                break
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析继续消息数据失败: {e}")
        
        except Exception as e:
            logger.error(f"继续消息错误: {e}")
            raise
    
    async def stop_generation(self) -> Dict[str, Any]:
        """停止生成"""
        try:
            response = await self.client.post(f"{self.base_url}/agents/messages/stop")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"停止生成失败: {e}")
            raise
    
    async def get_session_status(self) -> Dict[str, Any]:
        """获取会话状态"""
        try:
            response = await self.client.get(f"{self.base_url}/test/session/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取会话状态失败: {e}")
            raise
    
    async def reset_session(self) -> Dict[str, Any]:
        """重置会话"""
        try:
            response = await self.client.post(f"{self.base_url}/test/session/reset")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"重置会话失败: {e}")
            raise
    
    async def configure_llm_error(self, error_rate: float, error_types: list) -> Dict[str, Any]:
        """配置LLM错误模拟"""
        try:
            data = {
                "error_rate": error_rate,
                "error_types": error_types
            }
            response = await self.client.post(
                f"{self.base_url}/test/llm/simulate-error",
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"配置LLM错误失败: {e}")
            raise
    
    async def configure_llm_delay(self, delay_per_token: float) -> Dict[str, Any]:
        """配置LLM延迟"""
        try:
            data = {"delay_per_token": delay_per_token}
            response = await self.client.post(
                f"{self.base_url}/test/llm/set-delay",
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"配置LLM延迟失败: {e}")
            raise
    
    async def get_retry_stats(self) -> Dict[str, Any]:
        """获取重试统计"""
        try:
            response = await self.client.get(f"{self.base_url}/test/retry/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取重试统计失败: {e}")
            raise
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
        logger.info("模拟客户端已关闭")


class DisconnectSimulator:
    """
    断连模拟器
    用于测试断连重连功能
    """
    
    def __init__(self, client: MockSSEClient):
        self.client = client
        self.disconnect_tasks = []
    
    async def simulate_disconnect_after(self, delay: float):
        """
        在指定延迟后模拟断连
        
        Args:
            delay: 延迟时间（秒）
        """
        logger.info(f"将在{delay}秒后模拟断连")
        
        async def disconnect():
            await asyncio.sleep(delay)
            # 强制关闭连接
            await self.client.client.aclose()
            self.client.client = httpx.AsyncClient(timeout=30.0)
            logger.info("模拟断连完成")
        
        task = asyncio.create_task(disconnect())
        self.disconnect_tasks.append(task)
        return task
    
    async def cleanup(self):
        """清理断连任务"""
        for task in self.disconnect_tasks:
            if not task.done():
                task.cancel()
        self.disconnect_tasks.clear()
