"""
流式传输测试
测试SSE连接建立和数据推送，验证Patch实时传输的正确性
"""
import pytest
import asyncio
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_client import MockSSEClient
from utils.logger import logger


@pytest.fixture
def mock_client():
    """模拟客户端fixture"""
    client = MockSSEClient("http://localhost:8080")
    yield client


@pytest.mark.asyncio
class TestStreaming:
    """流式传输测试类"""
    
    async def test_basic_sse_connection(self, mock_client):
        """测试基本SSE连接"""
        print("\n=== 测试基本SSE连接 ===")
        
        # 重置会话状态
        await mock_client.reset_session()
        
        # 配置较快的响应速度以加快测试
        await mock_client.configure_llm_delay(0.01)
        
        # 发送消息并接收SSE流
        message_content = "测试SSE连接"
        patches_received = []
        
        print(f"✓ 发送消息: {message_content}")
        
        async for event in mock_client.send_message(message_content, "SSE测试"):
            patches_received.append(event)
            data = event["data"]
            
            print(f"  📦 收到事件: {data['patch_type']}")
            if data['patch_type'] == 'thinking' and data['thinking_delta']:
                print(f"     思考: {data['thinking_delta'].strip()}")
            elif data['patch_type'] == 'content' and data['content_delta']:
                print(f"     内容: {data['content_delta']}")
            elif data['patch_type'] == 'action':
                print(f"     行动: {data['action_title']}")
            elif data['patch_type'] == 'complete':
                print(f"     完成: {data['finished']}")
                break
        
        # 验证接收到的patches
        print(f"✓ 总共接收到 {len(patches_received)} 个事件")
        
        assert len(patches_received) > 0
        
        # 验证事件类型
        patch_types = [event["data"]["patch_type"] for event in patches_received]
        print(f"✓ 事件类型序列: {patch_types}")
        
        assert "thinking" in patch_types or "content" in patch_types
        assert "complete" in patch_types
        
        # 验证最后一个事件是完成事件
        last_event = patches_received[-1]
        assert last_event["data"]["finished"] is True
        
        print("✓ 基本SSE连接验证通过")
    
    async def test_patch_order_and_content(self, mock_client):
        """测试Patch顺序和内容"""
        print("\n=== 测试Patch顺序和内容 ===")
        
        # 重置会话状态
        await mock_client.reset_session()
        await mock_client.configure_llm_delay(0.01)
        
        # 发送消息
        message_content = "请详细分析这个问题"
        
        thinking_content = ""
        main_content = ""
        action_info = None
        
        print(f"✓ 发送消息: {message_content}")
        
        async for event in mock_client.send_message(message_content, "内容测试"):
            data = event["data"]
            
            if data['patch_type'] == 'thinking':
                thinking_content += data.get('thinking_delta', '')
                print(f"  🧠 思考增量: {data.get('thinking_delta', '').strip()}")
            
            elif data['patch_type'] == 'content':
                main_content += data.get('content_delta', '')
                print(f"  💬 内容增量: {data.get('content_delta', '')}")
            
            elif data['patch_type'] == 'action':
                action_info = {
                    'title': data.get('action_title'),
                    'params': data.get('action_params', {})
                }
                print(f"  🎯 行动: {action_info['title']}")
                print(f"     参数: {action_info['params']}")
            
            elif data['patch_type'] == 'complete':
                print(f"  ✅ 完成")
                break
        
        # 验证内容不为空
        print(f"✓ 思考内容长度: {len(thinking_content)}")
        print(f"✓ 主要内容长度: {len(main_content)}")
        print(f"✓ 行动信息: {action_info}")
        
        assert len(thinking_content) > 0 or len(main_content) > 0
        
        # 如果有行动，验证行动信息
        if action_info:
            assert action_info['title'] is not None
            assert isinstance(action_info['params'], dict)
        
        print("✓ Patch顺序和内容验证通过")
    
    async def test_message_history_api(self, mock_client):
        """测试消息历史API"""
        print("\n=== 测试消息历史API ===")
        
        # 重置会话状态
        await mock_client.reset_session()
        await mock_client.configure_llm_delay(0.01)
        
        # 发送第一条消息
        print("✓ 发送第一条消息")
        async for event in mock_client.send_message("第一条测试消息", "消息1"):
            if event["data"]["finished"]:
                break
        
        # 发送第二条消息（不等待完成）
        print("✓ 开始发送第二条消息")
        message_task = asyncio.create_task(
            self._consume_stream(mock_client.send_message("第二条测试消息", "消息2"))
        )
        
        # 等待一小段时间确保第二条消息开始生成
        await asyncio.sleep(0.1)
        
        # 获取消息历史
        history = await mock_client.get_message_history()
        
        print(f"✓ 消息历史包含 {len(history['messages'])} 条消息")
        for i, msg in enumerate(history['messages']):
            print(f"  {i+1}. [{msg['role']}] {msg['title']}: {msg['status']}")
        
        print(f"✓ 未完成消息ID: {history['incomplete_message_id']}")
        
        # 验证消息历史
        assert len(history['messages']) >= 2
        assert history['incomplete_message_id'] is not None  # 应该有未完成消息
        
        # 等待第二条消息完成
        await message_task
        
        print("✓ 消息历史API验证通过")
    
    async def test_continue_message(self, mock_client):
        """测试继续未完成消息"""
        print("\n=== 测试继续未完成消息 ===")
        
        # 重置会话状态
        await mock_client.reset_session()
        await mock_client.configure_llm_delay(0.05)  # 稍慢一点以便测试
        
        # 开始发送消息但不等待完成
        print("✓ 开始发送消息")
        message_task = asyncio.create_task(
            self._consume_stream(mock_client.send_message("测试继续消息功能", "继续测试"))
        )
        
        # 等待消息开始生成
        await asyncio.sleep(0.2)
        
        # 获取当前消息历史
        history = await mock_client.get_message_history()
        incomplete_id = history['incomplete_message_id']
        
        print(f"✓ 未完成消息ID: {incomplete_id}")
        assert incomplete_id is not None
        
        # 模拟重新连接继续接收消息
        print("✓ 模拟重连继续接收消息")
        continue_events = []
        
        async for event in mock_client.continue_message(incomplete_id):
            continue_events.append(event)
            data = event["data"]
            
            print(f"  📦 继续事件: {data['patch_type']}")
            
            if data["finished"]:
                break
        
        # 等待原始任务完成
        await message_task
        
        # 验证继续接收的事件
        print(f"✓ 继续接收到 {len(continue_events)} 个事件")
        assert len(continue_events) > 0
        
        # 验证有同步事件或内容事件
        event_types = [event["data"]["patch_type"] for event in continue_events]
        print(f"✓ 继续事件类型: {event_types}")
        
        assert any(t in ["sync", "thinking", "content", "complete"] for t in event_types)
        
        print("✓ 继续未完成消息验证通过")
    
    async def test_concurrent_connections(self, mock_client):
        """测试多个并发连接"""
        print("\n=== 测试多个并发连接 ===")
        
        # 重置会话状态
        await mock_client.reset_session()
        await mock_client.configure_llm_delay(0.02)
        
        # 注意：在这个简化的测试中，我们模拟多个连接
        # 实际上是同一个客户端的多个请求
        
        async def send_and_count(message, title):
            """发送消息并统计事件"""
            events = []
            async for event in mock_client.send_message(message, title):
                events.append(event)
                if event["data"]["finished"]:
                    break
            return len(events)
        
        # 由于我们的架构设计，同时只能有一个生成任务
        # 所以这里测试串行处理
        print("✓ 测试连续多个请求")
        
        tasks = []
        for i in range(3):
            # 等待前一个完成再开始下一个
            if i > 0:
                await asyncio.sleep(0.1)
            
            task = send_and_count(f"并发测试消息 {i+1}", f"并发{i+1}")
            event_count = await task
            
            print(f"  消息 {i+1} 完成，事件数: {event_count}")
            assert event_count > 0
        
        print("✓ 多个连接处理验证通过")
    
    async def test_stop_generation(self, mock_client):
        """测试停止生成功能"""
        print("\n=== 测试停止生成功能 ===")
        
        # 重置会话状态
        await mock_client.reset_session()
        await mock_client.configure_llm_delay(0.1)  # 较慢的响应以便测试停止
        
        # 开始发送消息
        print("✓ 开始发送消息")
        events_before_stop = []
        
        async def receive_with_stop():
            """接收消息同时在一定时间后停止"""
            async for event in mock_client.send_message("这是一个会被停止的长消息", "停止测试"):
                events_before_stop.append(event)
                # 在收到一些事件后停止
                if len(events_before_stop) >= 2:
                    print("  🛑 发送停止信号")
                    stop_result = await mock_client.stop_generation()
                    print(f"  停止结果: {stop_result}")
                    break
                
                if event["data"]["finished"]:
                    break
        
        await receive_with_stop()
        
        # 验证停止功能
        print(f"✓ 停止前收到 {len(events_before_stop)} 个事件")
        assert len(events_before_stop) >= 1
        
        # 检查会话状态
        status = await mock_client.get_session_status()
        print(f"✓ 停止后会话状态: {status}")
        
        # 验证不再生成
        assert status["is_generating"] is False
        
        print("✓ 停止生成功能验证通过")
    
    async def _consume_stream(self, stream):
        """辅助方法：消费流直到完成"""
        async for event in stream:
            if event["data"]["finished"]:
                break
