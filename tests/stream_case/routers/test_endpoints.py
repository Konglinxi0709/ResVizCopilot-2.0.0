"""
测试专用接口
提供调试和测试功能的接口
"""
from fastapi import APIRouter, HTTPException

from models.request_response import (
    SessionStatus, ErrorConfig, DelayConfig, RetryStats,
    QueueStatus, DisconnectConfig
)
from routers.agents import session_manager, agent
from utils.logger import logger

router = APIRouter(prefix="/test", tags=["测试接口"])


@router.get("/session/status", response_model=SessionStatus)
async def get_session_status():
    """获取当前会话的详细状态信息"""
    status = session_manager.get_status()
    
    response = SessionStatus(
        message_count=status["message_count"],
        current_message_id=status["current_message_id"],
        is_generating=status["is_generating"],
        queue_size=status["queue_size"]
    )
    
    logger.info(f"会话状态查询: {response.dict()}")
    return response


@router.post("/llm/simulate-error")
async def simulate_llm_error(config: ErrorConfig):
    """配置MockLLM模拟网络错误"""
    agent.configure_llm(
        error_rate=config.error_rate,
        error_types=config.error_types
    )
    
    logger.info(f"配置LLM错误模拟: {config.dict()}")
    return {"status": "ok", "message": f"已配置错误率: {config.error_rate}"}


@router.post("/session/reset")
async def reset_session():
    """清空消息历史，重置会话状态"""
    # 先停止当前生成任务
    if agent.is_generating():
        await agent.stop_generation()
    
    # 重置会话状态
    session_manager.reset()
    
    # 重置其他组件
    agent.action_handler.reset_database()
    agent.retry_wrapper.reset_stats()
    
    logger.info("会话状态已重置")
    return {"status": "ok", "message": "会话已重置"}


@router.get("/retry/stats", response_model=RetryStats)
async def get_retry_stats():
    """获取重试机制的统计信息"""
    stats = agent.retry_wrapper.get_retry_stats()
    
    response = RetryStats(
        total_attempts=stats["total_attempts"],
        successful_attempts=stats["successful_attempts"],
        failed_attempts=stats["failed_attempts"],
        average_delay=stats["average_delay"]
    )
    
    logger.info(f"重试统计查询: {response.dict()}")
    return response


@router.post("/llm/set-delay")
async def set_llm_delay(config: DelayConfig):
    """设置MockLLM的响应延迟"""
    agent.configure_llm(delay_per_token=config.delay_per_token)
    
    logger.info(f"设置LLM延迟: {config.delay_per_token}秒/token")
    return {"status": "ok", "message": f"已设置延迟: {config.delay_per_token}秒/token"}


@router.get("/queue/status", response_model=QueueStatus)
async def get_queue_status():
    """获取消息队列的当前状态"""
    status = session_manager.get_status()
    
    # 统计等待中的patch数量（简化实现）
    pending_patches = 0
    for subscriber_queue in session_manager._subscribers:
        pending_patches += subscriber_queue.qsize()
    
    response = QueueStatus(
        queue_size=status["queue_size"],
        pending_patches=pending_patches,
        active_connections=len(session_manager._subscribers)
    )
    
    logger.info(f"队列状态查询: {response.dict()}")
    return response


@router.post("/connection/disconnect")
async def force_disconnect(config: DisconnectConfig):
    """模拟SSE连接断开，用于测试重连机制"""
    # 这个接口主要用于测试，实际的断开连接由客户端模拟
    logger.info(f"模拟连接断开配置: {config.disconnect_after}秒后断开")
    return {
        "status": "ok", 
        "message": f"已配置{config.disconnect_after}秒后断开连接（需客户端配合）"
    }


@router.get("/stats/all")
async def get_all_stats():
    """获取所有组件的统计信息"""
    session_status = session_manager.get_status()
    agent_stats = agent.get_stats()
    
    all_stats = {
        "session": session_status,
        "agent": agent_stats,
        "timestamp": session_manager.messages.get(
            session_manager.current_message_id, {}
        ).__dict__.get("updated_at", None)
    }
    
    logger.info("查询所有统计信息")
    return all_stats
