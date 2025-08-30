"""
工程管理路由
提供工程级别的管理功能，支持工程的保存、加载、版本控制等
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.project_manager import shared_project_manager
from backend.utils.logger import logger

router = APIRouter(prefix="/projects", tags=["projects"])

# 使用共享的项目管理器实例
pm = shared_project_manager

@router.post("")
async def create_project(project_name: str):
    """
    创建新工程
    
    Args:
        project_name: 工程名称
        
    Returns:
        创建结果
    """
    try:
        result = pm.create_new_project(project_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"创建工程失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建工程失败: {str(e)}")

@router.post("/save")
async def save_current_project():
    """
    保存当前工程
    
    Returns:
        保存结果
    """
    try:
        result = pm.save_current_project()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"保存当前工程失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存当前工程失败: {str(e)}")

@router.post("/save-as")
async def save_as_current_project(new_project_name: str):
    """
    将当前工程另存为
    
    Args:
        new_project_name: 新的工程名称
        
    Returns:
        另存为结果
    """
    try:
        result = pm.save_as_current_project(new_project_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"另存为工程失败: {e}")
        raise HTTPException(status_code=500, detail=f"另存为工程失败: {str(e)}")

@router.get("/{project_name}")
async def load_project(project_name: str):
    """
    加载指定工程
    
    Args:
        project_name: 工程名称
        
    Returns:
        加载结果
    """
    try:
        result = pm.load_project(project_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"加载工程失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载工程失败: {str(e)}")

@router.get("")
async def list_projects():
    """
    获取工程列表
    
    Returns:
        工程列表
    """
    try:
        result = pm.list_projects()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"获取工程列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工程列表失败: {str(e)}")

@router.delete("/{project_name}")
async def delete_project(project_name: str):
    """
    删除指定工程
    
    Args:
        project_name: 工程名称
        
    Returns:
        删除结果
    """
    try:
        result = pm.delete_project(project_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"删除工程失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除工程失败: {str(e)}")

@router.get("/current/info")
async def get_current_project_info():
    """
    获取当前工程信息
    
    Returns:
        当前工程信息
    """
    try:
        return pm.get_current_project_info()
        
    except Exception as e:
        logger.error(f"获取当前工程信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取当前工程信息失败: {str(e)}")

@router.get("/current/full-data")
async def get_current_project_full_data():
    """
    获取当前工程的完整数据，包括消息历史和工程信息
    这个接口完全保留 /agents/messages/history 的数据格式，并添加工程相关信息
    
    Returns:
        包含消息历史和工程信息的完整数据
    """
    try:
        result = pm.get_current_project_full_data()
        logger.info(f"返回工程完整数据: {result['project_info']['project_name']}, {len(result['messages'])}条消息")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取当前工程完整数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取当前工程完整数据失败: {str(e)}")
