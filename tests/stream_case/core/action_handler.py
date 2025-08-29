"""
行动识别与处理器
从消息内容中识别行动指令并执行模拟操作
"""
import json
import re
from typing import Dict, List, Optional
from uuid import uuid4

from utils.logger import logger


class ActionHandler:
    """
    行动识别与处理器
    
    功能：
    1. 解析LLM输出中的行动指令
    2. 执行模拟的数据库操作
    3. 返回操作结果和模拟的snapshot_id
    """
    
    def __init__(self):
        """初始化行动处理器"""
        self.mock_database: Dict = {}  # 模拟数据库
        self.operation_count = 0  # 操作计数
        
        logger.info("行动处理器初始化完成")
    
    def parse_actions(self, action_data: dict) -> Optional[Dict]:
        """
        解析行动数据
        
        Args:
            action_data: 从LLM输出中解析的行动数据
            
        Returns:
            解析后的行动字典，如果解析失败返回None
        """
        try:
            if not isinstance(action_data, dict):
                return None
            
            if "title" not in action_data or "params" not in action_data:
                return None
            
            action = {
                "title": action_data["title"],
                "params": action_data["params"]
            }
            
            logger.info(f"解析行动指令: {action['title']}")
            return action
            
        except Exception as e:
            logger.error(f"解析行动指令失败: {e}")
            return None
    
    def execute_action(self, action_title: str, action_params: Dict) -> Dict:
        """
        执行行动指令
        
        Args:
            action_title: 行动标题
            action_params: 行动参数
            
        Returns:
            包含执行结果的字典
        """
        self.operation_count += 1
        result = {
            "success": True,
            "message": "",
            "snapshot_id": "",
            "operation_id": self.operation_count
        }
        
        try:
            if action_title == "create_research_problem":
                result.update(self._mock_create_problem(action_params))
            elif action_title == "create_solution":
                result.update(self._mock_create_solution(action_params))
            elif action_title == "update_problem":
                result.update(self._mock_update_problem(action_params))
            elif action_title == "delete_problem":
                result.update(self._mock_delete_problem(action_params))
            else:
                # 未知行动类型，但仍然返回成功结果
                result.update({
                    "message": f"执行了未知行动: {action_title}",
                    "snapshot_id": self._generate_snapshot_id()
                })
            
            logger.info(f"执行行动成功: {action_title} -> {result['snapshot_id']}")
            
        except Exception as e:
            result.update({
                "success": False,
                "message": f"执行行动失败: {str(e)}",
                "snapshot_id": ""
            })
            logger.error(f"执行行动失败: {action_title} - {e}")
        
        return result
    
    def _mock_create_problem(self, params: Dict) -> Dict:
        """模拟创建研究问题"""
        problem_id = str(uuid4())
        snapshot_id = self._generate_snapshot_id()
        
        problem_data = {
            "id": problem_id,
            "title": params.get("title", "未命名问题"),
            "significance": params.get("significance", ""),
            "criteria": params.get("criteria", ""),
            "created_at": "2024-01-01T00:00:00"
        }
        
        self.mock_database[f"problem_{problem_id}"] = problem_data
        
        return {
            "message": f"成功创建研究问题: {problem_data['title']}",
            "snapshot_id": snapshot_id,
            "problem_id": problem_id
        }
    
    def _mock_create_solution(self, params: Dict) -> Dict:
        """模拟创建解决方案"""
        solution_id = str(uuid4())
        snapshot_id = self._generate_snapshot_id()
        
        solution_data = {
            "id": solution_id,
            "title": params.get("title", "未命名方案"),
            "content": params.get("content", ""),
            "problem_id": params.get("problem_id", ""),
            "created_at": "2024-01-01T00:00:00"
        }
        
        self.mock_database[f"solution_{solution_id}"] = solution_data
        
        return {
            "message": f"成功创建解决方案: {solution_data['title']}",
            "snapshot_id": snapshot_id,
            "solution_id": solution_id
        }
    
    def _mock_update_problem(self, params: Dict) -> Dict:
        """模拟更新问题"""
        problem_id = params.get("id", "")
        snapshot_id = self._generate_snapshot_id()
        
        if f"problem_{problem_id}" in self.mock_database:
            problem_data = self.mock_database[f"problem_{problem_id}"]
            problem_data.update(params)
            message = f"成功更新问题: {problem_data['title']}"
        else:
            message = f"更新问题 {problem_id}（模拟操作）"
        
        return {
            "message": message,
            "snapshot_id": snapshot_id
        }
    
    def _mock_delete_problem(self, params: Dict) -> Dict:
        """模拟删除问题"""
        problem_id = params.get("id", "")
        snapshot_id = self._generate_snapshot_id()
        
        if f"problem_{problem_id}" in self.mock_database:
            del self.mock_database[f"problem_{problem_id}"]
            message = f"成功删除问题: {problem_id}"
        else:
            message = f"删除问题 {problem_id}（模拟操作）"
        
        return {
            "message": message,
            "snapshot_id": snapshot_id
        }
    
    def _generate_snapshot_id(self) -> str:
        """生成模拟的快照ID"""
        return f"snapshot_{uuid4().hex[:8]}_{self.operation_count}"
    
    def get_database_state(self) -> Dict:
        """获取模拟数据库状态"""
        return {
            "items": dict(self.mock_database),
            "operation_count": self.operation_count
        }
    
    def reset_database(self) -> None:
        """重置模拟数据库"""
        self.mock_database.clear()
        self.operation_count = 0
        logger.info("模拟数据库已重置")
