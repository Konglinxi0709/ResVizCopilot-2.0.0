from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.message.schemas.message_models import FrontendMessage


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
