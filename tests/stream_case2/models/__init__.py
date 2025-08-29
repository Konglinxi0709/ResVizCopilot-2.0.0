"""
模型定义模块
包含消息模型、补丁模型、请求响应模型等
"""

from .message import Message, Patch, FrontendPatch
from .request_response import (
    SendMessageRequest, MessageHistoryResponse, StopResponse,
    SessionStatus, ErrorConfig, RetryStats
)

__all__ = [
    "Message", "Patch", "FrontendPatch",
    "SendMessageRequest", "MessageHistoryResponse", "StopResponse",
    "SessionStatus", "ErrorConfig", "RetryStats"
]

