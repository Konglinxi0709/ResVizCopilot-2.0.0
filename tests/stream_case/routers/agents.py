"""
智能体接口路由
实现原设计的智能体调用接口，支持SSE流式传输
"""
import asyncio
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from models.request_response import (
    SendMessageRequest, MessageHistoryResponse, StopResponse
)
from core.session_manager import SessionManager
from core.agent_coroutine import AgentCoroutine
from utils.logger import logger

# 全局实例（在实际项目中应该使用依赖注入）
session_manager = SessionManager()
agent = AgentCoroutine(session_manager)

router = APIRouter(prefix="/agents", tags=["智能体接口"])


@router.post("/messages", response_class=EventSourceResponse)
async def sse_send_message(request: SendMessageRequest):
    """
    发送用户消息，启动智能体协程，返回SSE流式响应
    
    Args:
        request: 发送消息请求
        
    Returns:
        SSE流式响应
    """
    logger.info(f"接收到用户消息: {request.content[:50]}...")
    
    # 检查是否正在生成
    if agent.is_generating():
        raise HTTPException(status_code=429, detail="智能体正在生成响应，请等待完成")
    
    async def event_stream():
        """SSE事件流生成器"""
        try:
            # 启动智能体处理
            await agent.process_user_message(request.content, request.title)
            
            # 订阅消息更新
            async for patch in session_manager.subscribe_patches():
                # 转换patch为SSE事件
                event_data = {
                    "message_id": patch.message_id,
                    "patch_type": patch.patch_type,
                    "thinking_delta": patch.thinking_delta,
                    "content_delta": patch.content_delta,
                    "title": patch.title,
                    "action_title": patch.action_title,
                    "action_params": patch.action_params,
                    "snapshot_id": patch.snapshot_id,
                    "finished": patch.finished
                }
                
                # 发送SSE事件
                yield {
                    "event": "patch",
                    "data": json.dumps(event_data, ensure_ascii=False)
                }
                
                # 如果消息完成，结束流
                if patch.finished and patch.patch_type in ["complete", "error"]:
                    logger.info(f"消息完成: {patch.message_id}")
                    break
                    
        except asyncio.CancelledError:
            logger.info("SSE连接被取消")
        except Exception as e:
            logger.error(f"SSE流处理出错: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False)
            }
    
    return EventSourceResponse(event_stream())


@router.get("/messages/history", response_model=MessageHistoryResponse)
async def get_message_history():
    """
    获取会话的消息历史，包括未完成消息的ID
    
    Returns:
        消息历史响应
    """
    messages = session_manager.get_message_history()
    incomplete_msg = session_manager.get_incomplete_message()
    
    response = MessageHistoryResponse(
        messages=messages,
        incomplete_message_id=incomplete_msg.id if incomplete_msg else None
    )
    
    logger.info(f"返回消息历史: {len(messages)}条消息")
    return response


@router.get("/messages/continue/{message_id}", response_class=EventSourceResponse)
async def sse_continue_message(message_id: str):
    """
    继续未完成的消息，先同步历史内容，再继续监听新内容
    
    Args:
        message_id: 要继续的消息ID
        
    Returns:
        SSE流式响应
    """
    logger.info(f"继续消息: {message_id}")
    
    # 检查消息是否存在
    message = session_manager.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    async def continue_stream():
        """继续消息的SSE流"""
        try:
            # 首先发送历史内容（如果消息正在生成中）
            if message.status == "generating":
                # 发送当前消息状态
                sync_data = {
                    "message_id": message_id,
                    "patch_type": "sync",
                    "thinking_delta": message.thinking,
                    "content_delta": message.content,
                    "title": message.title,
                    "action_title": message.action_title,
                    "action_params": message.action_params,
                    "snapshot_id": message.snapshot_id,
                    "finished": False
                }
                
                yield {
                    "event": "sync",
                    "data": json.dumps(sync_data, ensure_ascii=False)
                }
                
                # 继续监听新的patch
                async for patch in session_manager.subscribe_patches():
                    if patch.message_id == message_id:
                        event_data = {
                            "message_id": patch.message_id,
                            "patch_type": patch.patch_type,
                            "thinking_delta": patch.thinking_delta,
                            "content_delta": patch.content_delta,
                            "title": patch.title,
                            "action_title": patch.action_title,
                            "action_params": patch.action_params,
                            "snapshot_id": patch.snapshot_id,
                            "finished": patch.finished
                        }
                        
                        yield {
                            "event": "patch",
                            "data": json.dumps(event_data, ensure_ascii=False)
                        }
                        
                        if patch.finished:
                            break
            else:
                # 消息已完成，只发送完整内容
                complete_data = {
                    "message_id": message_id,
                    "patch_type": "complete",
                    "thinking_delta": message.thinking,
                    "content_delta": message.content,
                    "title": message.title,
                    "action_title": message.action_title,
                    "action_params": message.action_params,
                    "snapshot_id": message.snapshot_id,
                    "finished": True
                }
                
                yield {
                    "event": "complete",
                    "data": json.dumps(complete_data, ensure_ascii=False)
                }
                
        except asyncio.CancelledError:
            logger.info("继续消息的SSE连接被取消")
        except Exception as e:
            logger.error(f"继续消息时出错: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False)
            }
    
    return EventSourceResponse(continue_stream())


@router.post("/messages/stop", response_model=StopResponse)
async def stop_generation():
    """
    停止当前生成任务，取消智能体协程
    
    Returns:
        停止响应
    """
    if agent.is_generating():
        success = await agent.stop_generation()
        if success:
            logger.info("成功停止生成任务")
            return StopResponse(status="success", message="生成任务已停止")
        else:
            logger.warning("停止生成任务失败")
            return StopResponse(status="error", message="停止生成任务失败")
    else:
        return StopResponse(status="info", message="当前没有正在进行的生成任务")
