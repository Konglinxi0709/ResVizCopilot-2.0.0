"""
智能体接口路由
实现智能体调用接口，支持SSE流式传输和snapshot对象替换
"""
import asyncio
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.agents.message_models import (
    SendMessageRequest, MessageHistoryResponse, StopResponse
)
from backend.agents.project_manager import ProjectManager
from backend.agents.agent_base import AgentBase
from backend.agents.llm_client import DeepSeekReasonerClient, DeepSeekV3Client
from backend.database.DatabaseManager import DatabaseManager
from backend.utils.logger import logger


# 创建路由器
router = APIRouter(prefix="/agents", tags=["智能体接口"])

# 全局实例
database_manager = DatabaseManager()
project_manager = ProjectManager(database_manager)


# 在这里使用project_manager.register_agent()注册智能体


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
    
    # 获取指定的智能体
    agent = project_manager.get_agent(request.agent_name)
    if not agent:
        raise HTTPException(
            status_code=400, 
            detail=f"未找到智能体: {request.agent_name}"
        )
    
    # 检查是否正在生成
    if agent.is_processing():
        raise HTTPException(
            status_code=429, 
            detail="智能体正在处理中，请等待完成"
        )
    
    async def event_stream():
        """SSE事件流生成器"""
        try:
            # 启动智能体处理
            agent_task = asyncio.create_task(
                agent.process_user_message(request.content, request.title)
            )
            
            # 订阅消息更新
            async for patch in project_manager.subscribe_patches():
                # 检查智能体是否还在处理
                if not agent.is_processing():
                    # 智能体已完成，检查是否有错误
                    last_result = agent.get_last_task_result()
                    if last_result and last_result.get("status") == "error":
                        # 发送错误事件
                        yield {
                            "event": "error",
                            "data": json.dumps({
                                "error": last_result.get("error"),
                                "error_type": last_result.get("error_type")
                            }, ensure_ascii=False)
                        }
                    break
                
                # 发送patch事件
                yield {
                    "event": "patch",
                    "data": json.dumps(patch.model_dump(), ensure_ascii=False, default=str)
                }
            
            # 等待智能体任务完成
            try:
                await agent_task
            except Exception as e:
                logger.error(f"智能体任务执行出错: {e}")
                    
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
    messages = project_manager.get_message_history()
    incomplete_msg = project_manager.get_incomplete_message()
    
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
    message = project_manager.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    async def continue_stream():
        """继续消息的SSE流"""
        try:
            # 首先发送历史内容（如果消息正在生成中）
            if message.status == "generating":
                # 发送当前消息状态（模拟patch事件）
                sync_patch = {
                    "message_id": message_id,
                    "thinking_delta": message.thinking,
                    "content_delta": message.content,
                    "title": message.title,
                    "action_title": message.action_title,
                    "action_params": message.action_params,
                    "snapshot_id": message.snapshot_id,
                    "snapshot": None,  # 历史同步不需要snapshot对象
                    "finished": False,
                    "rollback": False
                }
                
                yield {
                    "event": "patch",
                    "data": json.dumps(sync_patch, ensure_ascii=False, default=str)
                }
                
                # 继续监听新的patch
                async for patch in project_manager.subscribe_patches():
                    if patch.message_id == message_id:
                        yield {
                            "event": "patch",
                            "data": json.dumps(patch.model_dump(), ensure_ascii=False, default=str)
                        }
                        
                        if patch.finished:
                            break
            else:
                # 消息已完成，发送完整内容（模拟patch事件）
                complete_patch = {
                    "message_id": message_id,
                    "thinking_delta": message.thinking,
                    "content_delta": message.content,
                    "title": message.title,
                    "action_title": message.action_title,
                    "action_params": message.action_params,
                    "snapshot_id": message.snapshot_id,
                    "snapshot": _get_snapshot_object(message.snapshot_id),
                    "finished": True,
                    "rollback": False
                }
                
                yield {
                    "event": "patch",
                    "data": json.dumps(complete_patch, ensure_ascii=False, default=str)
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
    # 获取所有智能体并停止正在处理的
    stopped_agents = []
    
    for agent_name, agent in project_manager._agents.items():
        if agent.is_processing():
            success = await agent.stop_processing()
            if success:
                stopped_agents.append(agent_name)
    
    if stopped_agents:
        logger.info(f"成功停止智能体: {stopped_agents}")
        return StopResponse(
            status="success", 
            message=f"已停止智能体: {', '.join(stopped_agents)}"
        )
    else:
        return StopResponse(
            status="info", 
            message="当前没有正在进行的生成任务"
        )


@router.get("/status")
async def get_agent_status():
    """
    获取智能体状态
    
    Returns:
        智能体状态信息
    """
    status = project_manager.get_status()
    
    # 添加智能体详细信息
    agent_details = {}
    for agent_name, agent in project_manager._agents.items():
        agent_details[agent_name] = agent.get_stats()
    
    status["agent_details"] = agent_details
    
    return status


def _get_snapshot_object(snapshot_id: str) -> Dict[str, Any]:
    """
    获取快照对象
    
    Args:
        snapshot_id: 快照ID
        
    Returns:
        快照对象，如果不存在返回None
    """
    if snapshot_id:
        return project_manager.get_database_snapshot(snapshot_id)
    return None
