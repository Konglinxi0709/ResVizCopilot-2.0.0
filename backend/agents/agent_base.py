"""
智能体抽象基类
定义智能体的基本接口和通用功能
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Type, Union, List
import asyncio
import inspect

from backend.message.schemas.message_models import Patch
from .llm_client import DeepSeekClient, DeepSeekReasonerClient, DeepSeekV3Client
from .retry_wrapper import RetryWrapper
from backend.utils.xml_parser import XMLParser, XMLValidationError
from backend.utils.logger import logger
from pydantic import BaseModel
from backend.database.database_manager import DatabaseManager

class AgentBase(ABC):
    """
    智能体抽象基类
    
    核心功能：
    1. 任务管理和状态维护
    2. LLM调用和输出解析
    3. 行动执行和错误处理
    4. 重试机制集成
    """
    
    def __init__(self, 
                 name: str,
                 publish_callback: Callable,
                 llm_client: Optional[DeepSeekClient] = None,
                 retry_wrapper: Optional[RetryWrapper] = None,
                 database_manager: Optional[DatabaseManager] = None,
                 get_visible_messages: Optional[Callable] = None):
        """
        初始化智能体
        
        Args:
            name: 智能体名称
            publish_callback: 发布patch的回调函数
            llm_client: LLM客户端
            retry_wrapper: 重试包装器
            execute_action_func: 执行数据库操作的函数
        """
        self.name = name
        self.publish_callback = publish_callback
        self.database_manager = database_manager
        self.get_visible_messages = get_visible_messages
        # 初始化组件
        self.llm_client = llm_client or DeepSeekReasonerClient(publish_callback)
        self.retry_wrapper = retry_wrapper or RetryWrapper()
        self.xml_parser = XMLParser()
        
        # 设置LLM客户端的回调函数
        self.llm_client.set_publish_callback(publish_callback)
        
        # 任务状态
        self._current_task: Optional[asyncio.Task] = None
        self.last_task_result: Optional[Dict[str, Any]] = None
        
        logger.info(f"智能体 {name} 初始化完成")
    
    async def process_user_message(self, content: str, title: str = "用户消息", other_params: Optional[Dict[str, Any]] = None) -> None:
        """
        处理用户消息的入口点
        
        Args:
            content: 用户消息内容
            title: 消息标题
            other_params: 其他参数，包含智能体需要的额外信息
        """
        problem_id = other_params.get("problem_id")
        solution_id = other_params.get("solution_id")
        # 创建用户消息
        user_patch = Patch(
            message_id=None,  # 创建新消息
            role="user",  # 明确指定为用户消息
            visible_node_ids=[],
            title=title,
            content_delta=content,
            finished=True
        )
        if problem_id:
            user_patch.visible_node_ids.append(problem_id)
        if solution_id:
            user_patch.visible_node_ids.append(solution_id)
        await self.publish_callback(user_patch)
        
        # 启动智能体处理任务（不等待）
        self._current_task = asyncio.create_task(
            self._run_agent_task(content, other_params)
        )
        
        logger.info(f"智能体 {self.name} 开始处理用户消息")
    
    async def _run_agent_task(self, user_content: str, other_params: Optional[Dict[str, Any]] = None) -> None:
        """
        运行智能体任务
        
        Args:
            user_content: 用户输入内容
            other_params: 其他参数
        """
        try:
            await self._agent_process(user_content, other_params)
            self.last_task_result = {"status": "success"}
        except asyncio.CancelledError:
            stop_all_agents_patch = Patch(
                message_id="-",
                content_delta="\n【用户中断】",
                finished=True,
            )
            await self.publish_callback(stop_all_agents_patch)
            self.last_task_result = {"status": "success"}
        except Exception as e:
            self.last_task_result = {
                "status": "error", 
                "error": str(e),
                "error_type": type(e).__name__
            }
            logger.error(f"智能体任务失败: {e}")
        finally:
            finish_patch = Patch(
                message_id=None,
                role="assistant",
                visible_node_ids=["-"],
                title="任务已完成",
                content_delta="任务已完成\n",
                finished=True,
                action_title = "finished"
            )
            await self.publish_callback(finish_patch)
    
    @abstractmethod
    async def _agent_process(self, user_content: str, other_params: Optional[Dict[str, Any]] = None) -> None:
        """
        智能体处理流程核心逻辑（抽象方法）
        
        Args:
            user_content: 用户输入内容
            other_params: 其他参数
        """
        pass

    def _get_visible_messages_string(self, node_id: str, node_type: str) -> str:
        """
        获取可见消息
        """
        visible_messages_list = self.get_visible_messages(node_id, node_type)
        message_strings = []
        if node_type == "solution":
            problem_id = self.database_manager.get_parent_node_id_query(node_id)["data"]["parent_node_id"]
        else:
            problem_id = node_id
        for i, message in enumerate(visible_messages_list):
            publisher = "用户"
            publisher_id = message["publisher"]
            if message["role"] == "assistant":
                if publisher_id:
                    publisher_node = self.database_manager.get_node_by_id_query(publisher_id)["data"]["node"]
                    if publisher_node["type"] == "solution":
                        publisher_id = self.database_manager.get_parent_node_id_query(publisher_id)["data"]["parent_node_id"]
                        publisher_node = self.database_manager.get_node_by_id_query(publisher_id)["data"]["node"]
                    publisher_title = publisher_node["title"]
                    if problem_id == publisher_id:
                        publisher = f"“{publisher_title}”问题的负责专家（你）"
                    else:
                        publisher = f"“{publisher_title}”问题的负责专家"
                else:
                    publisher = "系统消息"
            message_string = f"[{i+1}] 【发出者】:{publisher}\n"+ \
            f"    【消息标题】:{message['title']}\n"+ \
            f"    【消息内容】\n" + \
            f"{message['content']}"
            message_strings.append(message_string)
        return "="*60 + "\n" + ("-"*60+"\n").join(message_strings) + "\n" + "="*60

    
    async def _call_llm_with_retry(self, 
                                   prompt: str, 
                                   title: str, 
                                   publisher: str,
                                   visible_node_ids: List[str] = [],
                                   validator: Optional[Type[BaseModel]] = None) -> Union[str, BaseModel]:
        """
        调用LLM并支持重试，可选地进行XML解析和验证
        
        Args:
            prompt: 提示词
            title: 消息标题
            validator: 可选的Pydantic验证器，如果提供则解析XML并验证
            rollback_message_id: 重试时回溯的消息ID
            
        Returns:
            如果有验证器，返回验证后的BaseModel对象；否则返回原始字符串
        """
        # 发布LLM消息开始patch
        llm_message_id = await self._publish_llm_start_patch(title, publisher, visible_node_ids)
        
        if validator:
            # 有验证器：调用LLM + 解析 + 验证（全部在重试范围内）
            async def llm_parse_validate():
                # 调用LLM
                content = await self.llm_client.stream_generate(prompt, llm_message_id, publish_content=False)
                
                # 从内容中提取XML片段
                xml_fragment = self.xml_parser.extract_xml_from_content(content, "response")
                if not xml_fragment:
                    raise XMLValidationError("未找到XML response片段")
                
                # 解析XML为字典
                data_dict = self.xml_parser.xml_to_dict(xml_fragment)
                
                # 使用验证器验证
                validated_data = self.xml_parser.validate_with_pydantic(data_dict, validator)

                if hasattr(validated_data, "to_content"):
                    content = validated_data.to_content()

                content_patch = Patch(
                    message_id=llm_message_id,
                    content_delta=content
                )

                await self.publish_callback(content_patch)
                return validated_data
            
            # 使用重试包装器执行整个流程
            result = await self.retry_wrapper.execute_with_retry(
                llm_parse_validate,
                self.publish_callback,
                llm_message_id
            )
            
            return result
        else:
            # 无验证器：仅调用LLM（在重试范围内）
            content = await self.retry_wrapper.execute_with_retry(
                self.llm_client.stream_generate,
                self.publish_callback,
                llm_message_id,
                prompt,
                llm_message_id
            )
            
            return content
    
    async def _publish_llm_start_patch(self, title: str, publisher: str, visible_node_ids: List[str] = []) -> str:
        """
        发布LLM消息开始patch
        
        Args:
            title: 消息标题
            
        Returns:
            创建的消息ID
        """
        start_patch = Patch(
            message_id=None,  # 创建新消息
            role="assistant",  # 明确指定为智能体消息
            visible_node_ids=visible_node_ids,
            publisher=publisher,
            title=title
        )
        
        message_id = await self.publish_callback(start_patch)
        return message_id

    def _create_patch(self, title: str, content_delta: str, finished: bool = False) -> Any:
        """
        创建patch对象
        
        Args:
            title: 标题
            content_delta: 内容增量
            finished: 是否完成
            
        Returns:
            Patch对象
        """
        from backend.message.schemas.message_models import Patch
        
        return Patch(
            role="assistant",
            title=title,
            content_delta=content_delta,
            finished=finished
        )

    async def _publish_error_patch(self, error_message: str) -> None:
        """
        发布错误patch
        
        Args:
            error_message: 错误消息
        """
        patch = self._create_patch(
            title="处理失败",
            content_delta=f"错误: {error_message}",
            finished=True
        )
        
        await self.publish_callback(patch)
    
    async def _get_environment_info(self, problem_id: str, user_requirement: Optional[str]) -> Dict[str, str]:
        """
        获取环境信息
        
        Args:
            problem_id: 问题ID
            user_requirement: 用户要求
            
        Returns:
            环境信息字典
        """
        try:
            # 查询研究树全貌
            tree_result = self.database_manager.get_compact_text_tree_query()
            tree_text = tree_result.get("data", {}).get("tree_text", "研究树为空") if tree_result["success"] else "研究树为空"
            
            # 查询当前问题详情
            problem_result = self.database_manager.get_problem_detail_query(problem_id)
            problem_detail = problem_result.get("data", {}).get("detail", "当前研究问题为空") if problem_result["success"] else "当前研究问题为空"
            
            # 查询根问题信息
            root_problem_id = self.database_manager.get_root_problem_id_query(problem_id)["data"]["root_problem_id"]
            root_problem = self.database_manager.get_problem_detail_query(root_problem_id)["data"]["detail"]
            
            related_solutions = self.database_manager.get_related_solutions_query(problem_id)["data"]
            expert_solutions_of_all_ancestor_problems = "\n".join([
                self.database_manager.get_solution_detail_query(solution_id)["data"]["detail"] 
                for solution_id in related_solutions["ancestors"]
            ]) if related_solutions["ancestors"] else "无上级专家解决方案"
            other_solutions_of_current_problem = "\n".join([
                self.database_manager.get_solution_detail_query(solution_id)["data"]["detail"] 
                for solution_id in related_solutions["siblings"]
            ]) if related_solutions["siblings"] else "无其他解决方案"
            expert_solutions_of_all_descendant_problems = "\n".join([
                self.database_manager.get_solution_detail_query(solution_id)["data"]["detail"] 
                for solution_id in related_solutions["descendants"]
            ]) if related_solutions["descendants"] else "无后代解决方案"


            return {
                "current_research_tree_full_text": tree_text,
                "current_research_problem": problem_detail,
                "expert_solutions_of_all_ancestor_problems": expert_solutions_of_all_ancestor_problems,
                "other_solutions_of_current_problem": other_solutions_of_current_problem,
                "root_problem": root_problem,
                "expert_solutions_of_all_descendant_problems": expert_solutions_of_all_descendant_problems,
                "user_prompt": user_requirement or "无要求"
            }
        except Exception as e:
            logger.error(f"获取环境信息失败: {e}")
            raise e
    
    
    async def _execute_action(self, action_func: Callable, publisher: str, *args, **kwargs) -> Dict[str, Any]:
        """
        执行行动
        
        Args:
            action_type: 行动类型
            action_params: 行动参数
            
        Returns:
            执行结果
        """
        
        # 发布行动开始patch
        action_message_id = await self._publish_action_start_patch(action_func.__name__, publisher)
        
        try:
            logger.info(f"执行行动: {action_func.__name__} - {args} - {kwargs}")
            # 直接执行数据库操作（不使用重试）
            if inspect.iscoroutinefunction(action_func):
                result = await action_func(*args, **kwargs)
            else:
                result = action_func(*args, **kwargs)
            
            # 发布行动结果patch
            await self._publish_action_result_patch(action_message_id, action_func.__name__, result)
            
            return result
            
        except Exception as e:
            logger.error(f"执行行动失败: {action_func.__name__} - {e}")
            
            # 发布错误patch
            error_patch = Patch(
                message_id=action_message_id,
                title=f"{action_func.__name__} 执行失败",
                content_delta=f"执行失败: {str(e)}\n",
                finished=True
            )
            await self.publish_callback(error_patch)
            raise
    
    async def _publish_action_start_patch(self, action_type: str, publisher: str) -> str:
        """
        发布行动开始patch
        
        Args:
            action_type: 行动类型
            publisher: 消息发布者id
        Returns:
            行动消息ID
        """
        start_patch = Patch(
            message_id=None,  # 创建新消息
            role="assistant",  # 明确指定为智能体消息
            title=f"正在进行 {action_type}",
            publisher=publisher
        )
        
        message_id = await self.publish_callback(start_patch)
        return message_id
    
    async def _publish_action_result_patch(self, 
                                         message_id: str, 
                                         action_type: str, 
                                         result: Dict[str, Any]) -> None:
        """
        发布行动结果patch
        
        Args:
            message_id: 消息ID
            action_type: 行动类型
            result: 执行结果
        """
        success = result.get("success", False)
        message = result.get("message", "")
        snapshot_id = result.get("snapshot_id", "")
        
        if success:
            title = f"{action_type} 已成功完成"
        else:
            title = f"{action_type} 执行失败"
        
        result_patch = Patch(
            message_id=message_id,
            title=title,
            action_title=action_type,
            action_params=result.get("data", {}),
            snapshot_id=snapshot_id,
            content_delta=f"\n执行结果: {message}\n",
            finished=True
        )
        
        await self.publish_callback(result_patch)
    
    async def stop_processing(self) -> bool:
        """
        停止当前处理
        
        Returns:
            是否成功停止
        """
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
                logger.info(f"智能体 {self.name} 处理已停止")
                
                # 发布中断patch
                stop_patch = Patch(
                    message_id=None,  # 创建新消息
                    role="assistant",  # 明确指定为智能体消息
                    title="任务已中断",
                    content_delta="用户取消了当前任务\n",
                    finished=True
                )
                await self.publish_callback(stop_patch)
                
                return True
            except Exception as e:
                logger.error(f"停止智能体 {self.name} 时出错: {e}")
                return False
        
        return False
    
    def is_processing(self) -> bool:
        """检查是否正在处理"""
        return self._current_task is not None and not self._current_task.done()
    
    def get_last_task_result(self) -> Optional[Dict[str, Any]]:
        """获取上一个任务的结果"""
        return self.last_task_result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "is_processing": self.is_processing(),
            "last_task_result": self.last_task_result,
            "llm_stats": self.llm_client.get_stats(),
            "retry_stats": self.retry_wrapper.get_retry_stats()
        }
