"""
测试专用接口路由
提供测试和调试功能的接口
"""
from fastapi import APIRouter
from typing import Dict, Any

from models.request_response import (
    SessionStatus, ErrorConfig, RetryStats, DelayConfig,
    DisconnectConfig, QueueStatus
)
from routers.agents import project_manager, simple_agent
from utils.logger import logger

router = APIRouter(prefix="/test", tags=["测试接口"])


@router.get("/session/status", response_model=SessionStatus)
async def get_session_status():
    """
    获取当前会话的详细状态信息
    
    Returns:
        会话状态
    """
    status = project_manager.get_status()
    
    response = SessionStatus(
        message_count=status["message_count"],
        current_message_id=status["current_message_id"],
        is_generating=status["is_generating"],
        queue_size=status["queue_size"]
    )
    
    logger.info(f"返回会话状态: {response.model_dump()}")
    return response


@router.post("/llm/simulate-error")
async def simulate_llm_error(config: ErrorConfig):
    """
    配置MockLLM模拟网络错误
    
    Args:
        config: 错误配置
        
    Returns:
        操作状态
    """
    simple_agent.llm_client.simulate_error(
        config.error_rate,
        config.error_types
    )
    
    logger.info(f"配置LLM错误模拟: {config.model_dump()}")
    return {"status": "ok", "message": "错误模拟已配置"}


@router.post("/session/reset")
async def reset_session():
    """
    清空消息历史，重置会话状态
    
    Returns:
        操作状态
    """
    project_manager.reset()
    simple_agent.reset_conversation()
    
    logger.info("会话状态已重置")
    return {"status": "ok", "message": "会话已重置"}


@router.get("/retry/stats", response_model=RetryStats)
async def get_retry_stats():
    """
    获取重试机制的统计信息
    
    Returns:
        重试统计
    """
    stats = simple_agent.retry_wrapper.get_retry_stats()
    
    response = RetryStats(
        total_attempts=stats["total_attempts"],
        successful_attempts=stats["successful_attempts"],
        failed_attempts=stats["failed_attempts"],
        average_delay=stats["average_delay"]
    )
    
    logger.info(f"返回重试统计: {response.model_dump()}")
    return response


@router.post("/llm/set-delay")
async def set_llm_delay(config: DelayConfig):
    """
    设置MockLLM的响应延迟
    
    Args:
        config: 延迟配置
        
    Returns:
        操作状态
    """
    simple_agent.llm_client.set_delay(config.delay_per_token)
    
    logger.info(f"设置LLM延迟: {config.delay_per_token}秒/token")
    return {"status": "ok", "message": f"延迟已设置为 {config.delay_per_token}秒/token"}


@router.get("/queue/status", response_model=QueueStatus)
async def get_queue_status():
    """
    获取消息队列的当前状态
    
    Returns:
        队列状态
    """
    status = project_manager.get_status()
    
    response = QueueStatus(
        queue_size=status["queue_size"],
        subscriber_count=status["queue_size"],  # 订阅者数量等于队列大小
        pending_patches=0  # 简化实现，暂时返回0
    )
    
    logger.info(f"返回队列状态: {response.model_dump()}")
    return response


@router.post("/connection/disconnect")
async def simulate_disconnect(config: DisconnectConfig):
    """
    模拟SSE连接断开，用于测试重连机制
    
    Args:
        config: 断连配置
        
    Returns:
        操作状态
    """
    # 这里只是记录请求，实际的断连需要在客户端实现
    logger.info(f"收到断连模拟请求: {config.disconnect_after}秒后断连")
    return {
        "status": "ok", 
        "message": f"将在{config.disconnect_after}秒后模拟断连"
    }


@router.get("/agents/stats")
async def get_agents_stats():
    """
    获取所有智能体的统计信息
    
    Returns:
        智能体统计信息
    """
    stats = {}
    
    for agent_name, agent in project_manager._agents.items():
        stats[agent_name] = agent.get_stats()
    
    logger.info(f"返回智能体统计: {len(stats)}个智能体")
    return {
        "agents": stats,
        "database_state": project_manager.data_manager.get_database_state()
    }


@router.get("/database/state")
async def get_database_state():
    """
    获取数据库状态
    
    Returns:
        数据库状态
    """
    state = project_manager.data_manager.get_database_state()
    
    logger.info(f"返回数据库状态: {state}")
    return state


@router.post("/database/reset")
async def reset_database():
    """
    重置数据库
    
    Returns:
        操作状态
    """
    project_manager.data_manager.reset()
    
    logger.info("数据库已重置")
    return {"status": "ok", "message": "数据库已重置"}

