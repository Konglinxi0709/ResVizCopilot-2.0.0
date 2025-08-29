"""
请求响应模型定义
包含API接口的请求和响应数据结构
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .message import Message


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(description="消息内容")
    title: str = Field(default="用户消息", description="消息标题")
    agent_name: str = Field(default="default", description="调用的智能体名称")


class MessageHistoryResponse(BaseModel):
    """消息历史响应"""
    messages: List[Message] = Field(description="消息列表")
    incomplete_message_id: Optional[str] = Field(default=None, description="未完成消息ID")


class StopResponse(BaseModel):
    """停止响应"""
    status: str = Field(description="状态")
    message: str = Field(description="响应消息")


# 测试专用模型
class SessionStatus(BaseModel):
    """会话状态"""
    message_count: int = Field(description="消息数量")
    current_message_id: Optional[str] = Field(default=None, description="当前消息ID")
    is_generating: bool = Field(description="是否正在生成")
    queue_size: int = Field(description="队列大小")


class ErrorConfig(BaseModel):
    """错误配置"""
    error_rate: float = Field(default=0.3, description="错误概率")
    error_types: List[str] = Field(default=["network", "timeout", "api_error"], description="错误类型")


class RetryStats(BaseModel):
    """重试统计"""
    total_attempts: int = Field(description="总尝试次数")
    successful_attempts: int = Field(description="成功次数")
    failed_attempts: int = Field(description="失败次数")
    average_delay: float = Field(description="平均延迟")


class DelayConfig(BaseModel):
    """延迟配置"""
    delay_per_token: float = Field(default=0.05, description="每token延迟")


class DisconnectConfig(BaseModel):
    """断连配置"""
    disconnect_after: int = Field(default=5, description="多少秒后断连")


class QueueStatus(BaseModel):
    """队列状态"""
    queue_size: int = Field(description="队列大小")
    subscriber_count: int = Field(description="订阅者数量")
    pending_patches: int = Field(description="待处理补丁数量")

