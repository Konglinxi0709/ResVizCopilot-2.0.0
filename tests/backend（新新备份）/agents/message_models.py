"""
消息模型定义
包含Message、Patch和FrontendPatch的完整数据结构

设计要点：
1. 删除Patch的patch_type属性，根据字段有无自动判断操作类型
2. 添加rollback属性支持消息回溯
3. FrontendPatch支持snapshot对象替换
4. 添加visible_node_ids属性控制消息可见性
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field


class Message(BaseModel):
    """
    消息实体模型
    
    设计要求：
    1. 只有两种角色：智能体或用户 
    2. 状态只有完成和正在生成，中断也视为完成
    3. 不使用枚举类型，而是使用标题代表消息含义
    4. 包含标题、思考、内容三大板块，可以为空字符串，但必须有这些字段
    5. 包含行动标题、行动参数、快照id等字段
    6. 包含可见节点id列表，控制消息的可见性
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="消息唯一标识")
    role: str = Field(description="角色: 'user' | 'assistant'")
    publisher: Optional[str] = Field(default=None, description="消息发布者id, None代表系统或用户发布(由role区分), 否则为节点id")
    status: str = Field(description="状态: 'generating' | 'completed'")
    title: str = Field(default="", description="消息标题")
    thinking: str = Field(default="", description="思考过程")
    content: str = Field(default="", description="消息内容")
    action_title: str = Field(default="", description="行动标题")
    action_params: Dict[str, Any] = Field(default_factory=dict, description="行动参数")
    snapshot_id: str = Field(default="", description="快照ID")
    visible_node_ids: List[str] = Field(default_factory=list, description="可见节点ID列表，空列表表示全局可见")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updated_at = datetime.now()


class Patch(BaseModel):
    """
    更新补丁模型
    
    设计要点：
    1. 删除patch_type属性，根据字段有无自动判断操作类型
    2. 除思考、内容字段为增量添加外，其它字段均为替换更新
    3. 添加rollback属性支持消息回溯
    4. finished标志消息完成
    5. message_id为空时表示创建新消息
    6. role属性用于指定创建消息时的角色
    7. visible_node_ids属性用于控制消息可见性
    """
    message_id: Optional[str] = Field(default=None, description="消息ID，为空时创建新消息")
    
    # 增量更新字段
    thinking_delta: str = Field(default="", description="思考增量内容")
    content_delta: str = Field(default="", description="内容增量")
    
    # 替换更新字段
    role: Optional[str] = Field(default=None, description="消息角色: 'user' | 'assistant'，仅在创建新消息时必需")
    publisher: Optional[str] = Field(default=None, description="消息发布者id, None代表系统或用户发布(由role区分), 否则为节点id")
    title: Optional[str] = Field(default=None, description="消息标题（替换）")
    action_title: Optional[str] = Field(default=None, description="行动标题（替换）")
    action_params: Optional[Dict[str, Any]] = Field(default=None, description="行动参数（替换）")
    snapshot_id: Optional[str] = Field(default=None, description="快照ID（替换）")
    visible_node_ids: Optional[List[str]] = Field(default=None, description="可见节点ID列表（替换）")
    
    # 控制字段
    finished: bool = Field(default=False, description="是否完成")
    rollback: bool = Field(default=False, description="是否回溯（删除包括该消息在内的后续所有消息）")
    
    def apply_to_message(self, message: Message) -> None:
        """
        将补丁应用到消息上
        
        Args:
            message: 要更新的消息对象
        """
        # 增量更新
        if self.thinking_delta:
            message.thinking += self.thinking_delta
        if self.content_delta:
            message.content += self.content_delta
            
        # 替换更新
        if self.role is not None:
            message.role = self.role
        if self.publisher is not None:
            message.publisher = self.publisher
        if self.title is not None:
            message.title = self.title
        if self.action_title is not None:
            message.action_title = self.action_title
        if self.action_params is not None:
            message.action_params = self.action_params
        if self.snapshot_id is not None:
            message.snapshot_id = self.snapshot_id
        if self.visible_node_ids is not None:
            message.visible_node_ids = self.visible_node_ids
            
        # 更新状态
        if self.finished:
            message.status = "completed"
            
        # 更新时间戳
        message.update_timestamp()

class FrontendMessage(Message):
    """
    发送到前端的消息模型
    
    扩展功能：
    - 包含snapshot对象用于前端数据库更新
    """
    snapshot: Optional[Dict[str, Any]] = Field(default=None, description="快照对象（替换snapshot_id）")

    @classmethod
    def from_message(cls, message: Message, snapshot_obj: Optional[Dict[str, Any]] = None) -> "FrontendMessage":
        """
        从基础Message创建FrontendMessage
        """
        frontend_message = cls(**message.model_dump())
        if snapshot_obj:
            frontend_message.snapshot = snapshot_obj
        return frontend_message

class FrontendPatch(Patch):
    """
    发送到前端的补丁模型
    
    扩展功能：
    - 包含snapshot对象用于前端数据库更新
    """
    snapshot: Optional[Dict[str, Any]] = Field(default=None, description="快照对象（替换snapshot_id）")
    
    @classmethod
    def from_patch(cls, patch: Patch, snapshot_obj: Optional[Dict[str, Any]] = None) -> "FrontendPatch":
        """
        从基础Patch创建FrontendPatch
        
        Args:
            patch: 基础补丁对象
            snapshot_obj: 快照对象
            
        Returns:
            前端补丁对象
        """
        frontend_patch = cls(**patch.model_dump())
        if snapshot_obj:
            frontend_patch.snapshot = snapshot_obj
        return frontend_patch


# 请求响应模型
class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(description="消息内容")
    title: str = Field(default="用户消息", description="消息标题")
    agent_name: str = Field(default="auto_research_agent", description="调用的智能体名称")
    other_params: Optional[Dict[str, Any]] = Field(default=None, description="其他参数")


class MessageHistoryResponse(BaseModel):
    """消息历史响应"""
    messages: list[FrontendMessage] = Field(description="消息列表")
    incomplete_message_id: Optional[str] = Field(default=None, description="未完成消息ID")


class StopResponse(BaseModel):
    """停止响应"""
    status: str = Field(description="状态")
    message: str = Field(description="响应消息")
