"""
智能体抽象基类
定义智能体的基本接口和通用功能
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, Type, Union
import asyncio

from models.message import Patch
from core.llm_client import MockLLMClient
from core.retry_wrapper import RetryWrapper
from utils.xml_parser import XMLParser, XMLValidationError
from utils.logger import logger
from pydantic import BaseModel


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
                 llm_client: Optional[MockLLMClient] = None,
                 retry_wrapper: Optional[RetryWrapper] = None,
                 execute_action_func: Optional[Callable] = None):
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
        self.execute_action_func = execute_action_func
        
        # 初始化组件
        self.llm_client = llm_client or MockLLMClient(publish_callback)
        self.retry_wrapper = retry_wrapper or RetryWrapper()
        self.xml_parser = XMLParser()
        
        # 设置LLM客户端的回调函数
        self.llm_client.set_publish_callback(publish_callback)
        
        # 任务状态
        self._current_task: Optional[asyncio.Task] = None
        self.last_task_result: Optional[Dict[str, Any]] = None
        
        logger.info(f"智能体 {name} 初始化完成")
    
    async def process_user_message(self, content: str, title: str = "用户消息") -> None:
        """
        处理用户消息的入口点
        
        Args:
            content: 用户消息内容
            title: 消息标题
        """
        # 创建用户消息
        user_patch = Patch(
            message_id=None,  # 创建新消息
            title=title,
            content_delta=content,
            finished=True
        )
        await self.publish_callback(user_patch)
        
        # 启动智能体处理任务（不等待）
        self._current_task = asyncio.create_task(
            self._run_agent_task(content)
        )
        
        logger.info(f"智能体 {self.name} 开始处理用户消息")
    
    async def _run_agent_task(self, user_content: str) -> None:
        """
        运行智能体任务
        
        Args:
            user_content: 用户输入内容
        """
        try:
            await self._agent_process(user_content)
            self.last_task_result = {"status": "success"}
        except Exception as e:
            self.last_task_result = {
                "status": "error", 
                "error": str(e),
                "error_type": type(e).__name__
            }
            logger.error(f"智能体任务失败: {e}")
    
    @abstractmethod
    async def _agent_process(self, user_content: str) -> None:
        """
        智能体处理流程核心逻辑（抽象方法）
        
        Args:
            user_content: 用户输入内容
        """
        pass
    
    async def _call_llm_with_retry(self, 
                                   prompt: str, 
                                   title: str, 
                                   validator: Optional[Type[BaseModel]] = None,
                                   rollback_message_id: Optional[str] = None) -> Union[str, BaseModel]:
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
        llm_message_id = await self._publish_llm_start_patch(title)
        
        if validator:
            # 有验证器：调用LLM + 解析 + 验证（全部在重试范围内）
            async def llm_parse_validate():
                # 调用LLM
                content = await self.llm_client.stream_generate(prompt, llm_message_id)
                
                # 从内容中提取XML片段
                xml_fragment = self.xml_parser.extract_xml_from_content(content, "action")
                if not xml_fragment:
                    raise XMLValidationError("未找到XML action片段")
                
                # 解析XML为字典
                data_dict = self.xml_parser.xml_to_dict(xml_fragment)
                
                # 使用验证器验证
                validated_data = self.xml_parser.validate_with_pydantic(data_dict, validator)
                
                return validated_data
            
            # 使用重试包装器执行整个流程
            result = await self.retry_wrapper.execute_with_retry(
                llm_parse_validate,
                self.publish_callback,
                rollback_message_id
            )
            
            return result
        else:
            # 无验证器：仅调用LLM（在重试范围内）
            content = await self.retry_wrapper.execute_with_retry(
                self.llm_client.stream_generate,
                self.publish_callback,
                rollback_message_id,
                prompt,
                llm_message_id
            )
            
            return content
    

    
    async def _publish_llm_start_patch(self, title: str) -> str:
        """
        发布LLM消息开始patch
        
        Args:
            title: 消息标题
            
        Returns:
            创建的消息ID
        """
        start_patch = Patch(
            message_id=None,  # 创建新消息
            title=title
        )
        
        message_id = await self.publish_callback(start_patch)
        return message_id
    

    
    async def _execute_action(self, action_type: str, action_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行行动
        
        Args:
            action_type: 行动类型
            action_params: 行动参数
            
        Returns:
            执行结果
        """
        if not self.execute_action_func:
            raise ValueError("未设置execute_action_func")
        
        # 发布行动开始patch
        action_message_id = await self._publish_action_start_patch(action_type)
        
        try:
            # 直接执行数据库操作（不使用重试）
            result = self.execute_action_func(action_type, action_params)
            
            # 发布行动结果patch
            await self._publish_action_result_patch(action_message_id, action_type, result)
            
            return result
            
        except Exception as e:
            logger.error(f"执行行动失败: {action_type} - {e}")
            
            # 发布错误patch
            error_patch = Patch(
                message_id=action_message_id,
                title=f"{action_type} 执行失败",
                content_delta=f"执行失败: {str(e)}\n",
                finished=True
            )
            await self.publish_callback(error_patch)
            raise
    
    async def _publish_action_start_patch(self, action_type: str) -> str:
        """
        发布行动开始patch
        
        Args:
            action_type: 行动类型
            
        Returns:
            行动消息ID
        """
        start_patch = Patch(
            message_id=None,  # 创建新消息
            title=f"正在进行 {action_type}"
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
            except asyncio.CancelledError:
                logger.info(f"智能体 {self.name} 处理已停止")
                
                # 发布中断patch
                stop_patch = Patch(
                    message_id=None,  # 创建新消息
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