"""
API测试
测试FastAPI接口的功能
"""
import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from utils.logger import logger


class TestAPI:
    """API测试类"""
    
    @pytest.fixture
    def client(self):
        """测试客户端fixture"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """测试根路径"""
        print("\n=== 测试根路径 ===")
        
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "2.0.0"
        
        print(f"应用版本: {data['version']}")
        print(f"功能特性: {len(data['features'])}")
    
    def test_health_check(self, client):
        """测试健康检查"""
        print("\n=== 测试健康检查 ===")
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "stream_case2"
        
        print(f"服务状态: {data['status']}")
    
    def test_message_history(self, client):
        """测试消息历史接口"""
        print("\n=== 测试消息历史接口 ===")
        
        response = client.get("/agents/messages/history")
        assert response.status_code == 200
        
        data = response.json()
        assert "messages" in data
        assert "incomplete_message_id" in data
        
        print(f"历史消息数量: {len(data['messages'])}")
    
    def test_session_status(self, client):
        """测试会话状态接口"""
        print("\n=== 测试会话状态接口 ===")
        
        response = client.get("/test/session/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "message_count" in data
        assert "is_generating" in data
        assert "queue_size" in data
        
        print(f"消息数量: {data['message_count']}")
        print(f"是否生成中: {data['is_generating']}")
    
    def test_session_reset(self, client):
        """测试会话重置"""
        print("\n=== 测试会话重置 ===")
        
        response = client.post("/test/session/reset")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        
        print(f"重置结果: {data['message']}")
    
    def test_llm_configuration(self, client):
        """测试LLM配置接口"""
        print("\n=== 测试LLM配置接口 ===")
        
        # 设置延迟
        delay_config = {"delay_per_token": 0.01}
        response = client.post("/test/llm/set-delay", json=delay_config)
        assert response.status_code == 200
        
        # 配置错误模拟
        error_config = {
            "error_rate": 0.1,
            "error_types": ["network"]
        }
        response = client.post("/test/llm/simulate-error", json=error_config)
        assert response.status_code == 200
        
        print("LLM配置更新成功")
    
    def test_retry_stats(self, client):
        """测试重试统计接口"""
        print("\n=== 测试重试统计接口 ===")
        
        response = client.get("/test/retry/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_attempts" in data
        assert "successful_attempts" in data
        assert "failed_attempts" in data
        assert "average_delay" in data
        
        print(f"重试统计: {data}")
    
    def test_database_operations(self, client):
        """测试数据库操作接口"""
        print("\n=== 测试数据库操作接口 ===")
        
        # 获取数据库状态
        response = client.get("/test/database/state")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "operation_count" in data
        
        print(f"数据库项目数: {len(data['items'])}")
        print(f"操作计数: {data['operation_count']}")
        
        # 重置数据库
        response = client.post("/test/database/reset")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        
        print("数据库重置成功")
    
    def test_agents_stats(self, client):
        """测试智能体统计接口"""
        print("\n=== 测试智能体统计接口 ===")
        
        response = client.get("/test/agents/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert "database_state" in data
        
        print(f"注册的智能体: {list(data['agents'].keys())}")
    
    @pytest.mark.asyncio
    async def test_sse_message_sending(self):
        """测试SSE消息发送"""
        print("\n=== 测试SSE消息发送 ===")
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # 发送消息请求
            message_data = {
                "content": "测试SSE消息发送",
                "title": "SSE测试",
                "agent_name": "simple"
            }
            
            # 使用stream方式接收SSE
            async with ac.stream(
                "POST",
                "/agents/messages",
                json=message_data,
                headers={"Accept": "text/event-stream"}
            ) as response:
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
                
                events_received = 0
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # 移除"data: "前缀
                            events_received += 1
                            print(f"收到SSE事件: {data.get('operation_type', 'unknown')}")
                            
                            # 如果收到完成事件，结束
                            if data.get("finished") and data.get("operation_type") == "complete":
                                break
                                
                        except json.JSONDecodeError:
                            continue
                        
                        # 防止无限等待
                        if events_received > 50:
                            break
                
                print(f"总共收到 {events_received} 个SSE事件")
                assert events_received > 0, "应该收到至少一个SSE事件"
    
    @pytest.mark.asyncio
    async def test_message_continue(self):
        """测试消息继续接口"""
        print("\n=== 测试消息继续接口 ===")
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # 先发送一个消息
            message_data = {
                "content": "测试消息继续功能",
                "title": "继续测试",
                "agent_name": "simple"
            }
            
            # 发送消息并获取消息ID
            message_id = None
            async with ac.stream(
                "POST",
                "/agents/messages",
                json=message_data,
                headers={"Accept": "text/event-stream"}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if not message_id:
                                message_id = data.get("message_id")
                            
                            if data.get("finished"):
                                break
                        except json.JSONDecodeError:
                            continue
            
            assert message_id is not None, "应该获得消息ID"
            print(f"获得消息ID: {message_id}")
            
            # 测试继续消息
            async with ac.stream(
                "GET",
                f"/agents/messages/continue/{message_id}",
                headers={"Accept": "text/event-stream"}
            ) as response:
                assert response.status_code == 200
                
                continue_events = 0
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        continue_events += 1
                        if continue_events > 10:  # 防止无限等待
                            break
                
                print(f"继续消息收到 {continue_events} 个事件")
    
    def test_stop_generation(self, client):
        """测试停止生成"""
        print("\n=== 测试停止生成 ===")
        
        response = client.post("/agents/messages/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "message" in data
        
        print(f"停止结果: {data['message']}")


if __name__ == "__main__":
    # 运行特定测试
    pytest.main([__file__, "-v", "-s"])

