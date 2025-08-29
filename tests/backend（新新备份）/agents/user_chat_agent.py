"""
用户提问智能体
对应流程图中"用户对某个解决方案提出修改意见"入口
"""
import asyncio
from typing import Dict, Any, Optional, List

from .agent_base import AgentBase
from .prompts_and_validators.handle_modification_requests import (
    HANDLE_MODIFICATION_REQUESTS_PROMPT,
    HandleModificationRequestsResponse
)
from .prompts_and_validators.modify_solution import (
    MODIFY_THE_SOLUTION_PROMPT,
    ModifySolutionResponse
)
from backend.database.schemas.research_tree import ProblemNode, SolutionNode, NodeType, ProblemType
from backend.utils.logger import logger
from backend.database.database_manager import DatabaseManager

class UserChatAgent(AgentBase):
    """
    用户提问智能体
    
    核心功能：
    1. 分析用户对解决方案的反馈
    2. 决定是否修改解决方案
    3. 执行解决方案修改
    4. 与用户进行交互和澄清
    """
    
    def __init__(self, 
                 name: str = "user_chat_agent",
                 publish_callback=None,
                 llm_client=None,
                 retry_wrapper=None,    
                 database_manager: DatabaseManager = None,
                 get_visible_messages=None):
        super().__init__(name, publish_callback, llm_client, retry_wrapper, database_manager, get_visible_messages)
        

        logger.info(f"用户提问智能体 {name} 初始化完成")
    
    async def _agent_process(self, user_content: str, other_params: Optional[Dict[str, Any]] = None) -> None:
        """
        智能体处理流程核心逻辑
        
        Args:
            user_content: 用户输入内容
            other_params: 其他参数
        """
        try:
            # 从other_params中获取解决方案ID和反馈内容
            
            solution_id = other_params.get("solution_id")
            
            if not solution_id:
                raise ValueError("未找到解决方案ID")
            
            # 验证解决方案节点
            await self._validate_solution_node(solution_id)
            
            problem_id = self.database_manager.get_parent_node_id_query(solution_id)["data"]["parent_node_id"]
                        
            # 决定是否修改解决方案
            modification_decision = await self._handle_modification_requests(problem_id, solution_id, user_content)
            
            if modification_decision.decision == "accept":
                await self._modify_solution(problem_id, solution_id, modification_decision.modification_plan)
                
        except Exception as e:
            logger.error(f"用户提问智能体处理失败: {e}")
            await self._publish_error_patch(f"处理失败: {str(e)}")
    
    
    async def _validate_solution_node(self, solution_id: str) -> SolutionNode:
        """
        验证解决方案节点
        
        Args:
            solution_id: 解决方案ID
            
        Returns:
            解决方案节点
            
        Raises:
            ValueError: 节点不存在或类型不正确
        """

        # 查询解决方案节点详情
        result = self.database_manager.get_solution_detail_query(solution_id)
        if not result["success"]:
            raise ValueError(f"解决方案节点不存在: {solution_id}")

    
    async def _handle_modification_requests(self, problem_id: str, solution_id: str, modification_request: str) -> HandleModificationRequestsResponse:
        """
        决定是否修改解决方案
        
        Args:
            problem_id: 问题ID
            solution_id: 解决方案ID
            modification_request: 修改请求
            
        Returns:
            修改决策
        """
        try:
            # 获取环境信息
            message_list = self._get_visible_messages_string(solution_id, NodeType.SOLUTION)
            current_solution = self.database_manager.get_solution_detail_query(solution_id)["data"]["detail"]
            env_info = await self._get_environment_info(problem_id, modification_request)

            info = {**env_info, "supervisor_name": "用户", "modification_request": env_info["user_prompt"], 
                "current_solution": current_solution, "message_list": message_list}
            # 调用LLM进行决策
            modification_decision = await self._call_llm_with_retry(
                prompt=HANDLE_MODIFICATION_REQUESTS_PROMPT.format_map(info),
                title="处理修改请求",
                publisher=solution_id,
                visible_node_ids=[solution_id],
                validator=HandleModificationRequestsResponse
            )
            
            return modification_decision
            
        except Exception as e:
            logger.error(f"处理修改请求失败: {e}")
            raise e
    
    async def _modify_solution(self, problem_id: str, solution_id: str, modify_plan: str) -> None:
        """
        修改解决方案
        
        Args:
            feedback_analysis: 反馈分析结果
            modification_decision: 修改决策
        """
        try:
            env_info = await self._get_environment_info(problem_id, solution_id)
            current_solution = self.database_manager.get_solution_detail_query(solution_id)["data"]["detail"]
            message_list = self._get_visible_messages_string(solution_id, NodeType.SOLUTION)
            current_solution_children_request_map = self.database_manager.get_solution_children_request_map_by_title_query(solution_id)["data"]["children_request_map"]
            current_solution_sub_problem_list = str(list(current_solution_children_request_map.keys()))

            info = {**env_info, "supervisor_name": "用户", "modify_plan": modify_plan, "current_solution_sub_problem_list": current_solution_sub_problem_list,
                "current_solution": current_solution, "message_list": message_list}

            # 调用LLM进行决策
            modify_solution_response = await self._call_llm_with_retry(
                prompt=MODIFY_THE_SOLUTION_PROMPT.format_map(info),
                title="处理修改请求",
                publisher=solution_id,
                visible_node_ids=[solution_id],
                validator=ModifySolutionResponse
            )
            action, modify_solution_request = modify_solution_response.to_request(current_solution_children_request_map)
            if action == "update":
                await self._execute_action(self.database_manager.update_solution, solution_id, solution_id, modify_solution_request)
            elif action == "create":
                await self._execute_action(self.database_manager.create_solution, solution_id, problem_id, modify_solution_request)
        except Exception as e:
            logger.error(f"修改解决方案失败: {e}")
            await self._publish_error_patch(f"修改解决方案失败: {str(e)}")
    