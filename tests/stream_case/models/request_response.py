"""
请求响应模型定义
包含API接口的请求和响应数据模型
"""
from typing import List, Optional

from pydantic import BaseModel

from models.message import Message


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str
    title: str = "用户消息"


class MessageHistoryResponse(BaseModel):
    """消息历史响应"""
    messages: List[Message]
    incomplete_message_id: Optional[str] = None


class StopResponse(BaseModel):
    """停止生成响应"""
    status: str
    message: str


# 测试专用模型
class SessionStatus(BaseModel):
    """会话状态"""
    message_count: int
    current_message_id: Optional[str]
    is_generating: bool
    queue_size: int


class ErrorConfig(BaseModel):
    """错误配置"""
    error_rate: float = 0.3  # 错误概率
    error_types: List[str] = ["network", "timeout", "api_error"]


class DelayConfig(BaseModel):
    """延迟配置"""
    delay_per_token: float = 0.1  # 每个token的延迟（秒）


class RetryStats(BaseModel):
    """重试统计"""
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    average_delay: float


class QueueStatus(BaseModel):
    """队列状态"""
    queue_size: int
    pending_patches: int
    active_connections: int


class DisconnectConfig(BaseModel):
    """断连配置"""
    disconnect_after: float = 5.0  # 多少秒后断开连接
