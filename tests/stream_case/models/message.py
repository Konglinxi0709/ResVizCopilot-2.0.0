"""
消息模型定义
包含Message和Patch的完整数据结构
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Message(BaseModel):
    """
    消息实体模型
    
    设计要求：
    1. 只有两种角色：智能体或用户
    2. 状态只有完成和正在生成，中断也视为完成
    3. 不使用枚举类型，而是使用标题代表消息含义
    4. 包含标题、思考、内容，可以为空字符串，但必须有这些字段
    5. 包含行动标题、行动参数、快照id等字段
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="消息唯一标识")
    role: str = Field(description="角色: 'user' | 'assistant'")
    status: str = Field(description="状态: 'generating' | 'completed'")
    title: str = Field(default="", description="消息标题")
    thinking: str = Field(default="", description="思考过程")
    content: str = Field(default="", description="消息内容")
    action_title: str = Field(default="", description="行动标题")
    action_params: Dict = Field(default_factory=dict, description="行动参数")
    snapshot_id: str = Field(default="", description="快照ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()


class Patch(BaseModel):
    """
    更新补丁模型
    
    设计要求：
    1. 不使用枚举类型
    2. 除思考、内容字段为增量添加外，其它字段均为替换更新
    3. 如果包含行动标题，则应触发相应的函数调用
    4. 数据库行动结果中的snapshot id在传到前端时需要替换为快照对象
    """
    message_id: str = Field(description="消息ID")
    patch_type: str = Field(description="补丁类型: 'content' | 'thinking' | 'action' | 'complete' | 'retry' | 'error'")
    
    # 增量更新字段
    thinking_delta: str = Field(default="", description="思考增量内容")
    content_delta: str = Field(default="", description="内容增量")
    
    # 替换更新字段
    title: Optional[str] = Field(default=None, description="消息标题（替换）")
    action_title: Optional[str] = Field(default=None, description="行动标题（替换）")
    action_params: Optional[Dict] = Field(default=None, description="行动参数（替换）")
    snapshot_id: Optional[str] = Field(default=None, description="快照ID（替换）")
    
    # 状态字段
    finished: bool = Field(default=False, description="是否完成")
    
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
        if self.title is not None:
            message.title = self.title
        if self.action_title is not None:
            message.action_title = self.action_title
        if self.action_params is not None:
            message.action_params = self.action_params
        if self.snapshot_id is not None:
            message.snapshot_id = self.snapshot_id
            
        # 更新状态
        if self.finished:
            message.status = "completed"
            
        # 更新时间戳
        message.update_timestamp()
