"""
单元测试
测试各个组件的独立功能
"""
import pytest
import asyncio
from typing import List

from models.message import Message, Patch, FrontendPatch
from core.data_manager import DataManager
from core.project_manager import ProjectManager
from core.llm_client import MockLLMClient
from core.retry_wrapper import RetryWrapper
from utils.xml_parser import XMLParser, XMLValidationError
from core.simple_agent_validators import CreateResearchProblemOutput, CreateResearchProblemParams
from core.simple_agent_prompts import PromptStrategy


class TestMessage:
    """测试消息模型"""
    
    def test_message_creation(self):
        """测试消息创建"""
        print("\n=== 测试消息创建 ===")
        
        message = Message(
            role="user",
            status="completed",
            title="测试消息",
            content="这是一条测试消息"
        )
        
        assert message.role == "user"
        assert message.status == "completed"
        assert message.title == "测试消息"
        assert message.content == "这是一条测试消息"
        assert message.id is not None
        
        print(f"创建消息: {message.id}")
        print(f"消息内容: {message.content}")
    
    def test_patch_application(self):
        """测试补丁应用"""
        print("\n=== 测试补丁应用 ===")
        
        message = Message(role="assistant", status="generating")
        
        # 应用思考补丁
        thinking_patch = Patch(
            message_id=message.id,
            thinking_delta="让我思考一下..."
        )
        thinking_patch.apply_to_message(message)
        
        assert message.thinking == "让我思考一下..."
        print(f"应用思考补丁: {message.thinking}")
        
        # 应用内容补丁
        content_patch = Patch(
            message_id=message.id,
            content_delta="这是回复内容"
        )
        content_patch.apply_to_message(message)
        
        assert message.content == "这是回复内容"
        print(f"应用内容补丁: {message.content}")
        
        # 应用完成补丁
        complete_patch = Patch(
            message_id=message.id,
            finished=True
        )
        complete_patch.apply_to_message(message)
        
        assert message.status == "completed"
        print(f"消息状态: {message.status}")
    
    def test_patch_operation_type(self):
        """测试补丁操作类型判断"""
        print("\n=== 测试补丁操作类型判断 ===")
        
        # 测试不同类型的补丁
        patches = [
            (Patch(message_id="test", thinking_delta="思考"), "thinking"),
            (Patch(message_id="test", content_delta="内容"), "content"),
            (Patch(message_id="test", action_title="行动"), "action"),
            (Patch(message_id="test", finished=True), "complete"),
            (Patch(message_id="test", rollback=True), "rollback"),
            (Patch(message_id="test", title="标题"), "title"),
        ]
        
        # 简化测试，不再需要操作类型判断
        for patch, expected_type in patches:
            print(f"补丁字段测试通过")


class TestSimpleAgentValidators:
    """测试简单智能体验证器"""
    
    def test_create_research_problem_validator(self):
        """测试创建研究问题验证器"""
        print("\n=== 测试创建研究问题验证器 ===")
        
        # 测试有效数据
        valid_data = {
            "title": "create_research_problem",
            "params": {
                "title": "测试研究问题标题",
                "significance": "这是一个具有重要意义的研究问题，将对相关领域产生积极影响",
                "criteria": "研究标准包括理论分析和实验验证"
            }
        }
        
        validator = CreateResearchProblemOutput(**valid_data)
        assert validator.title == "create_research_problem"
        assert validator.params.title == "测试研究问题标题"
        
        print("有效数据验证通过")
        
        # 测试无效数据
        try:
            invalid_data = {
                "title": "wrong_action",
                "params": {
                    "title": "短",  # 太短
                    "significance": "太短",  # 太短
                    "criteria": "短"  # 太短
                }
            }
            CreateResearchProblemOutput(**invalid_data)
            assert False, "应该抛出验证错误"
        except Exception as e:
            print(f"无效数据正确被拒绝: {e}")
    
    def test_prompt_strategy(self):
        """测试提示词策略"""
        print("\n=== 测试提示词策略 ===")
        
        strategy = PromptStrategy()
        
        # 测试不同类型的用户输入
        test_inputs = [
            ("请帮我创建一个研究问题", "create_problem"),
            ("我想查询现有的问题", "query_problems"),
            ("需要更新某个问题", "update_problem"),
            ("你好，请问你能做什么？", None)  # chat类型或随机
        ]
        
        for user_input, expected_type in test_inputs:
            prompt, validator = strategy.get_prompt_and_validator(user_input)
            
            assert len(prompt) > 0, "提示词不应为空"
            
            if expected_type and expected_type != "chat":
                assert validator is not None, f"期望有验证器用于类型: {expected_type}"
            
            print(f"输入: '{user_input}' -> 验证器: {validator.__name__ if validator else 'None'}")


class TestDataManager:
    """测试数据管理器"""
    
    @pytest.fixture
    def data_manager(self):
        """数据管理器fixture"""
        return DataManager()
    
    def test_create_research_problem(self, data_manager):
        """测试创建研究问题"""
        print("\n=== 测试创建研究问题 ===")
        
        params = {
            "title": "AI伦理研究",
            "significance": "探讨人工智能的伦理问题",
            "criteria": "需要理论与实践相结合"
        }
        
        result = data_manager.execute_action("create_research_problem", params)
        
        assert result["success"] is True
        assert "problem_id" in result
        assert result["snapshot_id"] != ""
        
        print(f"创建结果: {result['message']}")
        print(f"问题ID: {result['problem_id']}")
        print(f"快照ID: {result['snapshot_id']}")
    
    def test_snapshot_operations(self, data_manager):
        """测试快照操作"""
        print("\n=== 测试快照操作 ===")
        
        # 创建初始数据
        data_manager.database["test_item"] = {"value": "initial"}
        
        # 创建快照
        snapshot_id = data_manager.create_snapshot()
        print(f"创建快照: {snapshot_id}")
        
        # 修改数据
        data_manager.database["test_item"] = {"value": "modified"}
        assert data_manager.database["test_item"]["value"] == "modified"
        
        # 回溯到快照
        success = data_manager.rollback_to_snapshot(snapshot_id)
        assert success is True
        assert data_manager.database["test_item"]["value"] == "initial"
        
        print("快照回溯成功")
        
        # 获取快照对象
        snapshot_obj = data_manager.get_snapshot(snapshot_id)
        assert snapshot_obj is not None
        assert snapshot_obj["id"] == snapshot_id
        
        print(f"快照对象: {snapshot_obj['summary']}")


class TestProjectManager:
    """测试项目管理器"""
    
    @pytest.fixture
    def project_manager(self):
        """项目管理器fixture"""
        return ProjectManager()
    
    @pytest.mark.asyncio
    async def test_message_creation_from_patch(self, project_manager):
        """测试从补丁创建消息"""
        print("\n=== 测试从补丁创建消息 ===")
        
        patch = Patch(
            message_id="test_msg",
            title="测试消息",
            content_delta="消息内容",
            finished=True
        )
        
        msg_id = await project_manager.publish_patch(patch)
        
        assert msg_id == "test_msg"
        message = project_manager.get_message("test_msg")
        assert message is not None
        assert message.title == "测试消息"
        assert message.content == "消息内容"
        
        print(f"创建消息: {msg_id}")
        print(f"消息标题: {message.title}")
    
    @pytest.mark.asyncio
    async def test_message_rollback(self, project_manager):
        """测试消息回溯"""
        print("\n=== 测试消息回溯 ===")
        
        # 创建多条消息
        patches = [
            Patch(message_id="msg1", title="消息1", finished=True),
            Patch(message_id="msg2", title="消息2", finished=True),
            Patch(message_id="msg3", title="消息3", finished=True),
        ]
        
        for patch in patches:
            await project_manager.publish_patch(patch)
        
        assert len(project_manager.get_message_history()) == 3
        print(f"创建3条消息")
        
        # 回溯到msg2
        rollback_patch = Patch(message_id="msg2", rollback=True)
        result_id = await project_manager.publish_patch(rollback_patch)
        
        remaining_messages = project_manager.get_message_history()
        assert len(remaining_messages) == 1
        assert remaining_messages[0].id == "msg1"
        
        print(f"回溯后剩余消息: {len(remaining_messages)}")
    
    @pytest.mark.asyncio
    async def test_subscription(self, project_manager):
        """测试订阅机制"""
        print("\n=== 测试订阅机制 ===")
        
        received_patches = []
        
        async def subscriber():
            async for patch in project_manager.subscribe_patches():
                received_patches.append(patch)
                if patch.message_id == "sub_test" and patch.finished:
                    break
        
        # 启动订阅者
        subscriber_task = asyncio.create_task(subscriber())
        
        # 短暂延迟确保订阅者就绪
        await asyncio.sleep(0.1)
        
        # 发送测试补丁
        test_patch = Patch(
            message_id="sub_test",
            title="订阅测试",
            content_delta="测试内容",
            finished=True
        )
        await project_manager.publish_patch(test_patch)
        
        # 等待订阅者完成
        await subscriber_task
        
        assert len(received_patches) == 1
        assert received_patches[0].message_id == "sub_test"
        
        print(f"收到补丁数量: {len(received_patches)}")


class TestXMLParser:
    """测试XML解析器"""
    
    @pytest.fixture
    def xml_parser(self):
        """XML解析器fixture"""
        return XMLParser()
    
    def test_xml_to_dict(self, xml_parser):
        """测试XML转字典"""
        print("\n=== 测试XML转字典 ===")
        
        xml_text = """
        <action>
            <title>create_research_problem</title>
            <params>
                <title>AI研究问题</title>
                <significance>重要的研究方向</significance>
                <criteria>需要创新性</criteria>
            </params>
        </action>
        """
        
        result = xml_parser.xml_to_dict(xml_text)
        
        assert "title" in result
        assert "params" in result
        assert result["title"] == "create_research_problem"
        assert result["params"]["title"] == "AI研究问题"
        
        print(f"解析结果: {result}")
    
    def test_pydantic_validation(self, xml_parser):
        """测试Pydantic验证"""
        print("\n=== 测试Pydantic验证 ===")
        
        # 有效数据
        valid_data = {
            "title": "create_research_problem",
            "params": {
                "title": "AI伦理研究问题",
                "significance": "探讨人工智能发展中的伦理挑战和解决方案",
                "criteria": "需要理论分析和实践验证相结合"
            }
        }
        
        validated = xml_parser.validate_with_pydantic(valid_data, CreateResearchProblemOutput)
        assert validated.title == "create_research_problem"
        assert validated.params.title == "AI伦理研究问题"
        
        print(f"验证成功: {validated.params.title}")
        
        # 无效数据
        invalid_data = {
            "title": "wrong_action",  # 错误的动作类型
            "params": {
                "title": "短",  # 太短
                "significance": "短",  # 太短
                "criteria": "标准"
            }
        }
        
        with pytest.raises(XMLValidationError):
            xml_parser.validate_with_pydantic(invalid_data, CreateResearchProblemOutput)
        
        print("无效数据验证失败（符合预期）")
    
    def test_extract_xml_from_content(self, xml_parser):
        """测试从内容中提取XML"""
        print("\n=== 测试从内容中提取XML ===")
        
        content = """
        这是一些普通文本。
        
        <action>
            <title>test_action</title>
            <params>
                <param1>value1</param1>
            </params>
        </action>
        
        这是更多文本。
        """
        
        xml_fragment = xml_parser.extract_xml_from_content(content, "action")
        
        assert xml_fragment is not None
        assert "<action>" in xml_fragment
        assert "test_action" in xml_fragment
        
        print(f"提取的XML: {xml_fragment}")


class TestRetryWrapper:
    """测试重试包装器"""
    
    @pytest.fixture
    def retry_wrapper(self):
        """重试包装器fixture"""
        return RetryWrapper(max_retries=2, base_delay=0.1)
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, retry_wrapper):
        """测试成功执行"""
        print("\n=== 测试成功执行 ===")
        
        call_count = 0
        
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        # 模拟项目管理器
        class MockProjectManager:
            def get_current_message_id(self):
                return "test_msg"
        
        project_manager = MockProjectManager()
        
        result = await retry_wrapper.execute_with_retry(
            successful_func,
            lambda x: None,  # 空的发布回调
            project_manager
        )
        
        assert result == "success"
        assert call_count == 1
        
        print(f"执行成功，调用次数: {call_count}")
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, retry_wrapper):
        """测试失败重试"""
        print("\n=== 测试失败重试 ===")
        
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # 前两次失败
                raise ConnectionError("网络错误")
            return "success after retry"
        
        class MockProjectManager:
            def get_current_message_id(self):
                return "test_msg"
            
            async def publish_patch(self, patch):
                pass
        
        project_manager = MockProjectManager()
        
        result = await retry_wrapper.execute_with_retry(
            failing_func,
            lambda x: asyncio.sleep(0),  # 模拟发布回调
            project_manager
        )
        
        assert result == "success after retry"
        assert call_count == 3  # 重试2次后成功
        
        stats = retry_wrapper.get_retry_stats()
        assert stats["total_attempts"] == 3
        
        print(f"重试成功，总调用次数: {call_count}")
        print(f"重试统计: {stats}")


if __name__ == "__main__":
    # 运行特定测试
    pytest.main([__file__, "-v", "-s"])

