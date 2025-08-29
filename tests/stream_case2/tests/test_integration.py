"""
集成测试
测试整个系统的端到端功能
"""
import asyncio
import pytest
from typing import List, Dict, Any
import json

from core.project_manager import ProjectManager
from core.data_manager import DataManager
from core.simple_agent import SimpleAgent
from models.message import Patch, FrontendPatch
from utils.logger import logger


class TestIntegration:
    """集成测试类"""
    
    @pytest.fixture
    async def setup_system(self):
        """设置测试系统"""
        # 创建组件
        data_manager = DataManager()
        project_manager = ProjectManager(data_manager)
        
        # 创建智能体
        agent = SimpleAgent(
            publish_callback=project_manager.publish_patch,
            execute_action_func=data_manager.execute_action
        )
        
        # 注册智能体
        project_manager.register_agent("test_agent", agent)
        
        return {
            "data_manager": data_manager,
            "project_manager": project_manager,
            "agent": agent
        }
    
    @pytest.mark.asyncio
    async def test_basic_message_flow(self, setup_system):
        """测试基本消息流程"""
        system = await setup_system
        project_manager = system["project_manager"]
        agent = system["agent"]
        
        print("\n=== 测试基本消息流程 ===")
        
        # 收集发布的patches
        received_patches = []
        
        async def patch_collector():
            async for patch in project_manager.subscribe_patches():
                received_patches.append(patch)
                print(f"收到patch: {patch.message_id}")
                if patch.finished:
                    break
        
        # 启动patch收集器
        collector_task = asyncio.create_task(patch_collector())
        
        # 发送用户消息
        await agent.process_user_message("请帮我创建一个关于AI技术的研究问题", "用户请求")
        
        # 等待处理完成
        await collector_task
        
        # 验证结果
        assert len(received_patches) > 0, "应该收到至少一个patch"
        
        # 验证消息历史
        messages = project_manager.get_message_history()
        assert len(messages) >= 2, "应该至少有用户消息和智能体消息"
        
        print(f"总共收到 {len(received_patches)} 个patches")
        print(f"消息历史包含 {len(messages)} 条消息")
        
        # 打印消息详情
        for i, msg in enumerate(messages):
            print(f"消息 {i+1}: {msg.role} - {msg.title}")
            if msg.content:
                print(f"  内容: {msg.content[:100]}...")
            if msg.thinking:
                print(f"  思考: {msg.thinking[:100]}...")
    
    @pytest.mark.asyncio
    async def test_xml_parsing_and_action_execution(self, setup_system):
        """测试XML解析和行动执行"""
        system = await setup_system
        project_manager = system["project_manager"]
        agent = system["agent"]
        
        print("\n=== 测试XML解析和行动执行 ===")
        
        # 收集所有patches
        all_patches = []
        
        async def full_collector():
            action_count = 0
            finished_count = 0
            async for patch in project_manager.subscribe_patches():
                all_patches.append(patch)
                print(f"收到patch: {patch.message_id}, finished: {patch.finished}, action: {patch.action_title}")
                
                # 如果是行动结果patch，检查snapshot
                if patch.action_title and patch.finished:
                    action_count += 1
                    print(f"  行动: {patch.action_title}")
                    if hasattr(patch, 'snapshot_id') and patch.snapshot_id:
                        print(f"  快照ID: {patch.snapshot_id}")
                
                # 统计完成的消息
                if patch.finished:
                    finished_count += 1
                
                # 当有足够的完成消息时结束（用户消息+助手回复+行动消息）
                if finished_count >= 3:
                    break
        
        # 启动收集器
        collector_task = asyncio.create_task(full_collector())
        
        # 发送包含行动的消息
        await agent.process_user_message(
            "请创建一个研究问题：智能体协程与流式传输解耦的技术方案研究",
            "创建研究问题请求"
        )
        
        # 等待处理完成
        await collector_task
        
        # 验证行动执行
        action_patches = [p for p in all_patches if p.action_title]
        assert len(action_patches) > 0, "应该执行至少一个行动"
        
        # 验证数据库状态
        db_state = system["data_manager"].get_database_state()
        assert db_state["operation_count"] > 0, "应该有数据库操作"
        
        print(f"执行了 {len(action_patches)} 个行动")
        print(f"数据库操作计数: {db_state['operation_count']}")
    
    @pytest.mark.asyncio
    async def test_error_retry_mechanism(self, setup_system):
        """测试错误重试机制"""
        system = await setup_system
        project_manager = system["project_manager"]
        agent = system["agent"]
        
        print("\n=== 测试错误重试机制 ===")
        
        # 配置LLM模拟错误
        agent.llm_client.simulate_error(0.5, ["network", "timeout"])
        
        # 收集patches
        retry_patches = []
        
        async def retry_collector():
            async for patch in project_manager.subscribe_patches():
                retry_patches.append(patch)
                print(f"收到patch: {patch.message_id}")
                
                if patch.finished:
                    break
        
        # 启动收集器
        collector_task = asyncio.create_task(retry_collector())
        
        # 发送消息
        await agent.process_user_message("测试重试机制", "重试测试")
        
        # 等待处理完成
        await collector_task
        
        # 检查重试统计
        retry_stats = agent.retry_wrapper.get_retry_stats()
        print(f"重试统计: {retry_stats}")
        
        # 重置错误模拟
        agent.llm_client.simulate_error(0.0, [])
        
        # 验证是否有重试相关的patches
        retry_related = [p for p in retry_patches if "重试" in (p.title or "")]
        print(f"重试相关patches: {len(retry_related)}")
    
    @pytest.mark.asyncio
    async def test_message_rollback(self, setup_system):
        """测试消息回溯功能"""
        system = await setup_system
        project_manager = system["project_manager"]
        
        print("\n=== 测试消息回溯功能 ===")
        
        # 创建一些消息
        msg1_patch = Patch(
            message_id="msg1",
            title="消息1",
            content_delta="这是第一条消息",
            finished=True
        )
        await project_manager.publish_patch(msg1_patch)
        
        msg2_patch = Patch(
            message_id="msg2",
            title="消息2",
            content_delta="这是第二条消息",
            finished=True
        )
        await project_manager.publish_patch(msg2_patch)
        
        msg3_patch = Patch(
            message_id="msg3",
            title="消息3",
            content_delta="这是第三条消息",
            finished=True
        )
        await project_manager.publish_patch(msg3_patch)
        
        print(f"创建消息前历史数量: {len(project_manager.get_message_history())}")
        
        # 回溯到msg2
        rollback_patch = Patch(
            message_id="msg2",
            rollback=True
        )
        result_msg_id = await project_manager.publish_patch(rollback_patch)
        
        # 验证回溯结果
        messages_after_rollback = project_manager.get_message_history()
        print(f"回溯后历史数量: {len(messages_after_rollback)}")
        print(f"最新消息ID: {result_msg_id}")
        
        assert len(messages_after_rollback) == 1, "回溯后应该只剩1条消息"
        assert messages_after_rollback[0].id == "msg1", "应该只剩第一条消息"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, setup_system):
        """测试并发操作"""
        system = await setup_system
        project_manager = system["project_manager"]
        
        print("\n=== 测试并发操作 ===")
        
        # 创建多个订阅者
        subscribers = []
        received_counts = []
        
        async def create_subscriber(subscriber_id: int):
            count = 0
            async for patch in project_manager.subscribe_patches():
                count += 1
                if patch.message_id == "concurrent_test" and patch.finished:
                    break
            received_counts.append(count)
            print(f"订阅者 {subscriber_id} 收到 {count} 个patches")
        
        # 启动多个订阅者
        for i in range(3):
            task = asyncio.create_task(create_subscriber(i))
            subscribers.append(task)
        
        # 短暂延迟确保订阅者就绪
        await asyncio.sleep(0.1)
        
        # 发送测试消息
        test_patch = Patch(
            message_id="concurrent_test",
            title="并发测试",
            content_delta="测试并发订阅",
            finished=True
        )
        await project_manager.publish_patch(test_patch)
        
        # 等待所有订阅者完成
        await asyncio.gather(*subscribers)
        
        # 验证所有订阅者都收到了消息
        assert len(received_counts) == 3, "应该有3个订阅者"
        assert all(count > 0 for count in received_counts), "所有订阅者都应该收到消息"
        
        print(f"订阅者接收数量: {received_counts}")


if __name__ == "__main__":
    # 运行特定测试
    pytest.main([__file__, "-v", "-s"])

