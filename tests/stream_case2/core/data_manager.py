"""
数据管理器
模拟数据库操作，提供数据存储和快照功能
"""
import json
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime

from utils.logger import logger


class DataManager:
    """
    数据管理器
    
    功能：
    1. 模拟数据库操作
    2. 支持快照创建和回溯
    3. 提供数据库操作接口
    """
    
    def __init__(self):
        """初始化数据管理器"""
        self.database: Dict[str, Any] = {}  # 模拟数据库
        self.snapshots: Dict[str, Dict[str, Any]] = {}  # 快照存储
        self.operation_count = 0  # 操作计数
        
        logger.info("数据管理器初始化完成")
    
    def create_snapshot(self) -> str:
        """
        创建数据库快照
        
        Returns:
            快照ID
        """
        snapshot_id = f"snapshot_{uuid4().hex[:8]}_{self.operation_count}"
        self.snapshots[snapshot_id] = json.loads(json.dumps(self.database))  # 深拷贝
        
        logger.debug(f"创建快照: {snapshot_id}")
        return snapshot_id
    
    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        获取快照对象
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            快照对象，如果不存在返回None
        """
        snapshot_data = self.snapshots.get(snapshot_id)
        if snapshot_data:
            # 返回包含元数据的快照对象
            return {
                "id": snapshot_id,
                "created_at": datetime.now().isoformat(),
                "data": snapshot_data,
                "summary": f"包含{len(snapshot_data)}个数据项"
            }
        return None
    
    def rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """
        回溯到指定快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            是否成功回溯
        """
        if snapshot_id in self.snapshots:
            self.database = json.loads(json.dumps(self.snapshots[snapshot_id]))  # 深拷贝
            logger.info(f"回溯到快照: {snapshot_id}")
            return True
        else:
            logger.error(f"快照不存在: {snapshot_id}")
            return False
    
    def execute_action(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据库操作
        
        Args:
            action_type: 操作类型
            params: 操作参数
            
        Returns:
            操作结果
        """
        self.operation_count += 1
        
        try:
            if action_type == "create_research_problem":
                return self._create_research_problem(params)
            elif action_type == "create_solution":
                return self._create_solution(params)
            elif action_type == "update_problem":
                return self._update_problem(params)
            elif action_type == "delete_problem":
                return self._delete_problem(params)
            elif action_type == "query_problems":
                return self._query_problems(params)
            else:
                # 未知操作类型
                snapshot_id = self.create_snapshot()
                return {
                    "success": True,
                    "message": f"执行了未知操作: {action_type}",
                    "snapshot_id": snapshot_id,
                    "operation_id": self.operation_count
                }
                
        except Exception as e:
            logger.error(f"执行数据库操作失败: {action_type} - {e}")
            return {
                "success": False,
                "message": f"操作失败: {str(e)}",
                "snapshot_id": "",
                "operation_id": self.operation_count
            }
    
    def _create_research_problem(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建研究问题"""
        problem_id = str(uuid4())
        
        problem_data = {
            "id": problem_id,
            "title": params.get("title", "未命名问题"),
            "significance": params.get("significance", ""),
            "criteria": params.get("criteria", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.database[f"problem_{problem_id}"] = problem_data
        snapshot_id = self.create_snapshot()
        
        logger.info(f"创建研究问题: {problem_data['title']}")
        
        return {
            "success": True,
            "message": f"成功创建研究问题: {problem_data['title']}",
            "snapshot_id": snapshot_id,
            "operation_id": self.operation_count,
            "problem_id": problem_id,
            "data": problem_data
        }
    
    def _create_solution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建解决方案"""
        solution_id = str(uuid4())
        
        solution_data = {
            "id": solution_id,
            "title": params.get("title", "未命名方案"),
            "content": params.get("content", ""),
            "problem_id": params.get("problem_id", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.database[f"solution_{solution_id}"] = solution_data
        snapshot_id = self.create_snapshot()
        
        logger.info(f"创建解决方案: {solution_data['title']}")
        
        return {
            "success": True,
            "message": f"成功创建解决方案: {solution_data['title']}",
            "snapshot_id": snapshot_id,
            "operation_id": self.operation_count,
            "solution_id": solution_id,
            "data": solution_data
        }
    
    def _update_problem(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """更新问题"""
        problem_id = params.get("id", "")
        key = f"problem_{problem_id}"
        
        if key in self.database:
            self.database[key].update(params)
            self.database[key]["updated_at"] = datetime.now().isoformat()
            message = f"成功更新问题: {self.database[key]['title']}"
            data = self.database[key]
        else:
            # 模拟操作
            data = {"id": problem_id, "title": params.get("title", "模拟问题")}
            message = f"更新问题 {problem_id}（模拟操作）"
        
        snapshot_id = self.create_snapshot()
        
        logger.info(message)
        
        return {
            "success": True,
            "message": message,
            "snapshot_id": snapshot_id,
            "operation_id": self.operation_count,
            "data": data
        }
    
    def _delete_problem(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """删除问题"""
        problem_id = params.get("id", "")
        key = f"problem_{problem_id}"
        
        if key in self.database:
            deleted_data = self.database.pop(key)
            message = f"成功删除问题: {deleted_data['title']}"
        else:
            message = f"删除问题 {problem_id}（模拟操作）"
            deleted_data = {"id": problem_id}
        
        snapshot_id = self.create_snapshot()
        
        logger.info(message)
        
        return {
            "success": True,
            "message": message,
            "snapshot_id": snapshot_id,
            "operation_id": self.operation_count,
            "deleted_data": deleted_data
        }
    
    def _query_problems(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询问题"""
        # 筛选出所有问题
        problems = {k: v for k, v in self.database.items() if k.startswith("problem_")}
        
        # 应用筛选条件
        keyword = params.get("keyword", "")
        if keyword:
            problems = {
                k: v for k, v in problems.items() 
                if keyword.lower() in v.get("title", "").lower()
            }
        
        snapshot_id = self.create_snapshot()
        
        logger.info(f"查询到{len(problems)}个问题")
        
        return {
            "success": True,
            "message": f"查询到{len(problems)}个问题",
            "snapshot_id": snapshot_id,
            "operation_id": self.operation_count,
            "problems": list(problems.values())
        }
    
    def get_database_state(self) -> Dict[str, Any]:
        """获取数据库状态"""
        return {
            "items": dict(self.database),
            "operation_count": self.operation_count,
            "snapshot_count": len(self.snapshots)
        }
    
    def reset(self) -> None:
        """重置数据管理器"""
        self.database.clear()
        self.snapshots.clear()
        self.operation_count = 0
        logger.info("数据管理器已重置")

