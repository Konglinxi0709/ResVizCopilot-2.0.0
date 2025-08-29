"""
项目管理器
负责一切与用户交互的接口，按需调用相应的智能体，统一消息操作接口
"""
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Callable
from uuid import uuid4
import json
from datetime import datetime

from backend.agents.message_models import Message, Patch, FrontendPatch, FrontendMessage
from backend.database.database_manager import DatabaseManager
from backend.utils.logger import log_multiline_text, logger

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class ProjectManager:
    """
    项目管理器
    
    核心职责：
    1. 统一消息操作接口（创建、更新、回溯都通过publish_patch完成）
    2. 维护消息队列和事件发布机制
    3. 管理智能体调用
    4. 提供数据管理器接口
    """
    
    def __init__(self, database_manager: Optional[DatabaseManager] = None):
        """
        初始化项目管理器
        
        Args:
            database_manager: 数据库管理器实例
        """
        self.messages: Dict[str, Message] = {}  # 消息存储
        self.message_order: List[str] = []  # 消息顺序
        self.database_manager = database_manager or DatabaseManager()  # 数据库管理器
        self._subscribers: List[asyncio.Queue] = []  # 订阅者队列列表
        self._agents: Dict[str, object] = {}  # 智能体实例字典
        
        logger.info("项目管理器初始化完成")
    
    def register_agent(self, name: str, agent_instance: object) -> None:
        """
        注册智能体实例
        
        Args:
            name: 智能体名称
            agent_instance: 智能体实例
        """
        self._agents[name] = agent_instance
        logger.info(f"注册智能体: {name}")
    
    def get_agent(self, name: str) -> Optional[object]:
        """
        获取智能体实例
        
        Args:
            name: 智能体名称
            
        Returns:
            智能体实例，如果不存在返回None
        """
        return self._agents.get(name)
    
    async def publish_patch(self, patch: Patch) -> str:
        """
        发布补丁，统一处理所有消息操作
        
        Args:
            patch: 补丁对象
            
        Returns:
            消息ID（如果是回滚，则返回回滚后剩余的最新消息ID）
            
        Raises:
            ValueError: 创建消息时存在正在生成的消息
        """
        logger.debug(f"接收到补丁: {patch}")
        if patch.action_title == "finished":
            await self._distribute_patch(patch)
            return

        # 处理回溯操作
        if patch.rollback:
            if not patch.message_id:
                raise ValueError("回溯操作必须指定message_id")
            return await self._handle_rollback(patch)
        
        # 如果message_id为空，创建新消息
        if patch.message_id is None:
            return await self._create_message_from_patch(patch)
        
        if patch.message_id == "-":
            return await self._update_all_messages(patch)

        # 检查消息是否存在
        message = self.messages.get(patch.message_id)
        
        if message is None:
            raise ValueError(f"消息不存在: {patch.message_id}")
        else:
            # 消息存在，更新消息
            return await self._update_existing_message(patch)

    def log_message_history(self) -> None:
        """
        日志消息历史
        """
        logger.info("\n" * 10)
        logger.info("=" * 100)
        logger.info("消息历史")
        logger.info("=" * 100)
        for message in self.get_message_history():
            logger.info(f"【消息】: {message.id}, 角色: {message.role}, 发送者: {message.publisher}")
            logger.info(f"- 标题: {message.title}")
            logger.info(f"- 状态: {message.status}")
            logger.info(f"- 思考: ")
            log_multiline_text(message.thinking)
            logger.info(f"- 内容: ")
            log_multiline_text(message.content)
            logger.info(f"- 行动标题: {message.action_title}")
            logger.info(f"- 行动参数: {message.action_params}")
            logger.info(f"- 快照ID: {message.snapshot_id}")
            logger.info(f"- 可见节点ID列表: {message.visible_node_ids}")
            logger.info(f"- 创建时间: {message.created_at}")
            logger.info(f"- 更新时间: {message.updated_at}")
            logger.info("-" * 100)
        logger.info("=" * 100)
        #current_snapshot = self.database_manager.get_current_snapshot()
        #log_multiline_text(f"当前数据库状态: \n{json.dumps(current_snapshot.model_dump(), indent=2, ensure_ascii=False, cls=DateTimeEncoder)}")
        logger.info("=" * 100 + "\n" * 10)

    async def _create_message_from_patch(self, patch: Patch) -> str:
        """
        从补丁创建新消息
        
        Args:
            patch: 补丁对象
            
        Returns:
            创建的消息ID
            
        Raises:
            ValueError: 存在正在生成的消息或缺少role属性
        """
        # 检查是否有消息正在生成
        generating_msg = self.get_incomplete_message()
        if generating_msg:
            raise ValueError(f"存在正在生成的消息: {generating_msg.id}")
        
        # 检查role属性是否存在
        if patch.role is None:
            raise ValueError("创建新消息时必须指定role属性")
        
        # 根据角色设置默认状态
        if patch.role == "user":
            default_status = "completed"  # 用户消息通常是完整的
        else:  # assistant
            default_status = "generating"  # 智能体消息通常开始时是生成中
        
        # 创建新消息
        message = Message(
            role=patch.role,
            status=default_status
        )
        
        # 更新patch的message_id为新生成的ID
        patch.message_id = message.id
        
        # 应用补丁
        patch.apply_to_message(message)
        
        # 存储消息
        self.messages[message.id] = message
        self.message_order.append(message.id)
        
        # 分发给订阅者
        await self._distribute_patch(patch)
        
        logger.info(f"创建新消息: {message.id}, 角色: {message.role}")
        return message.id

    async def _update_all_messages(self, patch: Patch) -> str:
        """
        更新所有消息
        """
        for message in self.messages.values():
            if message.status == "generating":
                patch.apply_to_message(message)
        await self._distribute_patch(patch)
        return self.message_order[-1] if self.message_order else ""
    
    async def _update_existing_message(self, patch: Patch) -> str:
        """
        更新现有消息
        
        Args:
            patch: 补丁对象
            
        Returns:
            消息ID
        """
        message = self.messages[patch.message_id]
        
        # 应用补丁
        patch.apply_to_message(message)
        
        # 分发给订阅者
        await self._distribute_patch(patch)
        
        logger.debug(f"更新消息: {message.id}")
        if message.status == "completed":
            logger.info("消息完成")
            self.log_message_history()
        return message.id
    
    async def _handle_rollback(self, patch: Patch) -> str:
        """
        处理消息回溯
        
        Args:
            patch: 补丁对象
            
        Returns:
            回溯后剩余的最新消息ID
        """
        # 找到消息在顺序中的位置
        try:
            rollback_index = self.message_order.index(patch.message_id)
        except ValueError:
            logger.warning(f"回溯消息不存在: {patch.message_id}")
            return self.message_order[-1] if self.message_order else ""
        
        # 删除从该位置开始的所有消息
        messages_to_remove = self.message_order[rollback_index+1:]
        for msg_id in messages_to_remove:
            if msg_id in self.messages:
                del self.messages[msg_id]
        
        # 更新消息顺序
        self.message_order = self.message_order[:rollback_index+1]
        
        target_message = self.messages[patch.message_id]
        target_message.status = "generating"
        target_message.content = ""
        target_message.thinking = ""
        target_message.updated_at = datetime.now()

        # 分发回溯通知
        await self._distribute_patch(patch)
        
        logger.info(f"回溯消息: 删除了 {len(messages_to_remove)} 条消息")
        self.log_message_history()
        # 返回剩余的最新消息ID
        return self.message_order[-1] if self.message_order else ""
    
    async def _distribute_patch(self, patch: Patch) -> None:
        """
        分发补丁给所有订阅者
        
        Args:
            patch: 补丁对象
        """
        # 处理快照对象替换
        frontend_patch = await self._process_patch_for_frontend(patch)
        logger.debug(f"当前订阅者数量: {len(self._subscribers)}")
        # 分发给所有订阅者
        for subscriber_queue in self._subscribers:
            try:
                await subscriber_queue.put(frontend_patch)
            except Exception as e:
                logger.error(f"分发补丁失败: {e}")
        logger.debug(f"分发补丁: {frontend_patch.message_id}")
    
    async def _process_patch_for_frontend(self, patch: Patch) -> FrontendPatch:
        """
        处理补丁以供前端使用（替换snapshot_id为snapshot对象）
        
        Args:
            patch: 原始补丁
            
        Returns:
            前端补丁对象
        """
        snapshot_obj = None
        # 如果有snapshot_id，获取对应的快照对象
        if patch.snapshot_id:
            snapshot_obj = self.get_database_snapshot(patch.snapshot_id)
        # 创建前端补丁
        frontend_patch = FrontendPatch.from_patch(patch, snapshot_obj)
        
        return frontend_patch

    def _process_message_for_frontend(self, message: Message) -> FrontendMessage:
        """
        处理消息以供前端使用（替换snapshot_id为snapshot对象）
        """
        snapshot_obj = None
        if message.snapshot_id:
            snapshot_obj = self.get_database_snapshot(message.snapshot_id)
        return FrontendMessage.from_message(message, snapshot_obj)
    
    async def subscribe_patches(self) -> AsyncGenerator[FrontendPatch, None]:
        """
        订阅补丁更新
        
        Yields:
            前端补丁对象
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
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """获取指定消息"""
        return self.messages.get(message_id)
    
    def get_message_history(self) -> List[Message]:
        """
        获取消息历史
        
        Returns:
            按创建顺序排序的消息列表
        """
        message_history = [self._process_message_for_frontend(self.messages[msg_id]) for msg_id in self.message_order if msg_id in self.messages]
        return message_history
    
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
    
    def get_current_message_id(self) -> Optional[str]:
        """获取当前最新消息ID"""
        return self.message_order[-1] if self.message_order else None
    
    def get_status(self) -> Dict:
        """
        获取项目状态
        
        Returns:
            包含统计信息的字典
        """
        incomplete_msg = self.get_incomplete_message()
        return {
            "message_count": len(self.messages),
            "current_message_id": self.get_current_message_id(),
            "is_generating": incomplete_msg is not None,
            "queue_size": len(self._subscribers),
            "registered_agents": list(self._agents.keys()),
            "database_state": self.get_database_state()
        }
    
    def reset(self) -> None:
        """重置项目状态"""
        self.messages.clear()
        self.message_order.clear()
        # 注意：这里不重置数据库管理器，因为它有自己的状态管理
        
        # 清空所有订阅者队列
        for queue in self._subscribers:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        
        logger.info("项目状态已重置")
    
    def get_database_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        """
        获取数据库快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            快照对象，如果不存在返回None
        """
        # 从数据库管理器获取快照
        snapshot = self.database_manager.snapshot_map.get(snapshot_id)
        if snapshot:
            return {
                "id": snapshot.id,
                "created_at": snapshot.created_at.isoformat(),
                "data": snapshot.model_dump(),
                "summary": f"包含{len(snapshot.roots)}个根问题"
            }
        return None
    
    def get_database_state(self) -> Dict:
        """获取数据库状态"""
        current_snapshot = self.database_manager.get_current_snapshot()
        return {
            "current_snapshot_id": current_snapshot.id,
            "snapshot_count": len(self.database_manager.snapshot_map),
            "root_problems_count": len(current_snapshot.roots)
        }
    
    def get_visible_messages(self, node_id: str, node_type: str) -> List[Dict[str, str]]:
        """
        获取指定节点可见的消息列表
        
        Args:
            node_id: 节点ID
            node_type: 节点类型 ('problem' 或 'solution')
            
        Returns:
            可见消息列表，每个消息包含role、title、content
        """
        visible_messages = []
        
        for message in self.get_message_history():
            # 检查消息是否可见
            if self._is_message_visible(message, node_id, node_type):
                visible_messages.append({
                    "role": message.role,
                    "publisher": message.publisher,
                    "title": message.title,
                    "content": message.content
                })
        
        return visible_messages
    
    def _is_message_visible(self, message: Message, node_id: str, node_type: str) -> bool:
        """
        判断消息是否对指定节点可见
        
        Args:
            message: 消息对象
            node_id: 节点ID
            node_type: 节点类型
            
        Returns:
            是否可见
        """
        # 全局可见消息
        if not message.visible_node_ids:
            return True
        
        # 节点直接可见
        if node_id in message.visible_node_ids:
            return True
        
        # 如果是解决方案节点，检查父问题是否可见
        if node_type == "solution":
            # 获取父问题ID
            parent_problem_id = self._get_parent_problem_id(node_id)
            if parent_problem_id and parent_problem_id in message.visible_node_ids:
                return True
        
        return False
    
    def _get_parent_problem_id(self, solution_id: str) -> Optional[str]:
        """
        获取解决方案的父问题ID
        
        Args:
            solution_id: 解决方案ID
            
        Returns:
            父问题ID，如果不存在返回None
        """
        current_snapshot = self.database_manager.get_current_snapshot()
        
        def find_parent_in_nodes(nodes: List) -> Optional[str]:
            for node in nodes:
                if hasattr(node, 'children'):
                    for child in node.children:
                        if child.id == solution_id:
                            return node.id
                    # 递归查找
                    result = find_parent_in_nodes(node.children)
                    if result:
                        return result
            return None
        
        return find_parent_in_nodes(current_snapshot.roots)