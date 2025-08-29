#!/usr/bin/env python3
"""
SSE调试程序
用于调试SSE事件流和patch数据
"""
import asyncio
import json
import requests
from sseclient import SSEClient

async def debug_sse():
    """调试SSE事件流"""
    print("🚀 开始SSE调试")
    
    # 1. 先创建根问题
    print("\n1. 创建根问题...")
    problem_data = {
        "title": "测试问题",
        "problem_type": "implementation",
        "significance": "",
        "criteria": ""
    }
    
    response = requests.post(
        "http://127.0.0.1:8008/research-tree/problems/root",
        json=problem_data
    )
    
    if response.status_code != 200:
        print(f"❌ 创建根问题失败: {response.status_code}")
        return
    
    problem_id = response.json()["snapshot"]["roots"][-1]["id"]
    print(f"✅ 根问题创建成功，ID: {problem_id}")
    
    # 2. 调用智能体
    print(f"\n2. 调用智能体，问题ID: {problem_id}")
    
    agent_request = {
        "content": f"问题ID: {problem_id}\n要求: 无特殊要求",
        "title": "测试调用",
        "agent_name": "auto_research_agent"
    }
    
    print(f"请求数据: {json.dumps(agent_request, ensure_ascii=False, indent=2)}")
    
    response = requests.post(
        "http://127.0.0.1:8008/agents/messages",
        json=agent_request,
        stream=True
    )
    
    if response.status_code != 200:
        print(f"❌ 调用智能体失败: {response.status_code}")
        print(f"响应: {response.text}")
        return
    
    print("✅ 智能体调用成功，开始接收SSE流...")
    
    # 3. 处理SSE流
    print("\n3. 处理SSE事件流...")
    
    try:
        client = SSEClient(response)
        
        for event in client.events():
            print(f"\n📡 收到事件: {event.event}")
            print(f"   数据: {event.data[:200]}{'...' if len(event.data) > 200 else ''}")
            
            if event.event == "patch":
                try:
                    patch_data = json.loads(event.data)
                    print(f"   ✅ Patch解析成功")
                    print(f"   - message_id: {patch_data.get('message_id')}")
                    print(f"   - role: {patch_data.get('role')}")
                    print(f"   - title: {patch_data.get('title')}")
                    print(f"   - finished: {patch_data.get('finished')}")
                    print(f"   - thinking_delta: {patch_data.get('thinking_delta', '')[:50]}...")
                    print(f"   - content_delta: {patch_data.get('content_delta', '')[:50]}...")
                except json.JSONDecodeError as e:
                    print(f"   ❌ Patch JSON解析失败: {e}")
                    print(f"   原始数据: {event.data}")
            
            elif event.event == "error":
                try:
                    error_data = json.loads(event.data)
                    print(f"   ❌ 错误事件: {error_data}")
                except json.JSONDecodeError:
                    print(f"   ❌ 错误事件解析失败: {event.data}")
            
            # 限制事件数量，避免无限循环
            if event.event == "patch" and patch_data.get("finished", False):
                print("\n✅ 收到完成事件，停止接收")
                break
                
    except Exception as e:
        print(f"❌ 处理SSE流时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_sse())
