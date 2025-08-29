"""
会话管理器
管理消息会话，维护消息历史和状态，提供消息队列机制
"""
import asyncio
from typing import Dict, List, Optional, AsyncGenerator
from uuid import uuid4

from models.message import Message, Patch
from utils.logger import logger


class SessionManager:
    """
    会话管理器
    
    职责：
    1. 管理消息历史和状态
    2. 提供消息队列和事件发布机制
    3. 支持多消费者模式的消息分发
    """
    
    def __init__(self):
        """初始化会话管理器"""
        self.messages: Dict[str, Message] = {}  # 消息存储
        self.current_message_id: Optional[str] = None  # 当前消息ID
        self.event_queue: asyncio.Queue = asyncio.Queue()  # 事件队列
        self._subscribers: List[asyncio.Queue] = []  # 订阅者队列列表
        
        logger.info("会话管理器初始化完成")
    
    def create_message(self, role: str, title: str = "") -> Message:
        """
        创建新消息
        
        Args:
            role: 消息角色 ('user' | 'assistant')
            title: 消息标题
            
        Returns:
            创建的消息对象
        """
        message = Message(
            role=role,
            status="completed" if role == "user" else "generating",
            title=title
        )
        
        self.messages[message.id] = message
        self.current_message_id = message.id
        
        logger.info(f"创建新消息: {message.id}, 角色: {role}, 标题: {title}")
        return message
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """获取指定消息"""
        return self.messages.get(message_id)
    
    def update_message(self, message_id: str, patch: Patch) -> Message:
        """
        使用补丁更新消息
        
        Args:
            message_id: 消息ID
            patch: 更新补丁
            
        Returns:
            更新后的消息对象
            
        Raises:
            KeyError: 消息不存在
        """
        message = self.messages.get(message_id)
        if not message:
            raise KeyError(f"消息不存在: {message_id}")
        
        # 应用补丁
        patch.apply_to_message(message)
        
        logger.debug(f"更新消息 {message_id}: {patch.patch_type}")
        return message
    
    def get_message_history(self) -> List[Message]:
        """
        获取消息历史
        
        Returns:
            按创建时间排序的消息列表
        """
        messages = list(self.messages.values())
        messages.sort(key=lambda m: m.created_at)
        return messages
    
    def get_incomplete_message(self) -> Optional[Message]:
        """
        获取未完成的消息
        
        Returns:
            状态为generating的消息，如果没有则返回None
        """
        for message in self.messages.values():
            if message.status == "generating":
                return message
        return None
    
    async def publish_patch(self, patch: Patch) -> None:
        """
        发布补丁到消息队列
        
        Args:
            patch: 要发布的补丁
        """
        # 更新消息
        try:
            self.update_message(patch.message_id, patch)
        except KeyError:
            logger.error(f"发布补丁失败，消息不存在: {patch.message_id}")
            return
        
        # 分发给所有订阅者
        for subscriber_queue in self._subscribers:
            try:
                await subscriber_queue.put(patch)
            except Exception as e:
                logger.error(f"分发补丁失败: {e}")
        
        logger.debug(f"发布补丁: {patch.patch_type} -> {patch.message_id}")
    
    async def subscribe_patches(self) -> AsyncGenerator[Patch, None]:
        """
        订阅补丁更新
        
        Yields:
            补丁对象
        """
        subscriber_queue = asyncio.Queue()
        self._subscribers.append(subscriber_queue)
        
        logger.info(f"新订阅者加入，当前订阅者数量: {len(self._subscribers)}")
        
        try:
            while True:
                patch = await subscriber_queue.get()
                yield patch
        except asyncio.CancelledError:
            logger.info("订阅者断开连接")
        finally:
            # 清理订阅者
            if subscriber_queue in self._subscribers:
                self._subscribers.remove(subscriber_queue)
            logger.info(f"订阅者移除，当前订阅者数量: {len(self._subscribers)}")
    
    def get_current_message_id(self) -> Optional[str]:
        """获取当前消息ID"""
        return self.current_message_id
    
    def get_status(self) -> Dict:
        """
        获取会话状态
        
        Returns:
            包含统计信息的字典
        """
        incomplete_msg = self.get_incomplete_message()
        return {
            "message_count": len(self.messages),
            "current_message_id": self.current_message_id,
            "is_generating": incomplete_msg is not None,
            "queue_size": len(self._subscribers)
        }
    
    def reset(self) -> None:
        """重置会话状态"""
        self.messages.clear()
        self.current_message_id = None
        # 清空所有订阅者队列
        for queue in self._subscribers:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        
        logger.info("会话状态已重置")
