#!/usr/bin/env python3
"""
集成测试脚本
验证流式传输技术案例的各项功能
"""
import asyncio
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, '.')

from tests.mock_client import MockSSEClient
from utils.logger import logger


async def test_basic_message_flow():
    """测试基本消息流程"""
    print("\n🔄 测试基本消息流程")
    
    client = MockSSEClient("http://localhost:8080")
    
    try:
        # 重置会话
        await client.reset_session()
        print("✓ 会话已重置")
        
        # 配置较快的响应速度
        await client.configure_llm_delay(0.02)
        print("✓ LLM延迟已配置")
        
        # 发送消息
        content = "请帮我分析一下这个技术验证案例的设计"
        
        print(f"📤 发送消息: {content}")
        
        patches_received = 0
        thinking_content = ""
        main_content = ""
        action_title = None
        
        async for event in client.send_message(content, "集成测试"):
            patches_received += 1
            data = event["data"]
            
            print(f"📦 [{patches_received}] {data['patch_type']}", end="")
            
            if data['patch_type'] == 'thinking' and data['thinking_delta']:
                thinking_content += data['thinking_delta']
                print(f" - 思考: {data['thinking_delta'].strip()}")
            elif data['patch_type'] == 'content' and data['content_delta']:
                main_content += data['content_delta']
                print(f" - 内容: {data['content_delta']}")
            elif data['patch_type'] == 'action':
                action_title = data['action_title']
                print(f" - 行动: {action_title}")
            elif data['patch_type'] == 'complete':
                print(f" - 完成")
                break
            else:
                print()
        
        print(f"\n✅ 消息流程测试完成:")
        print(f"   - 收到 {patches_received} 个patch")
        print(f"   - 思考内容长度: {len(thinking_content)}")
        print(f"   - 主要内容长度: {len(main_content)}")
        print(f"   - 行动标题: {action_title}")
        
        # 验证基本要求
        assert patches_received > 0, "应该收到至少一个patch"
        assert len(thinking_content) > 0 or len(main_content) > 0, "应该有思考或内容"
        
        return True
        
    except Exception as e:
        print(f"❌ 基本消息流程测试失败: {e}")
        return False
    finally:
        await client.close()


async def test_retry_mechanism():
    """测试重试机制"""
    print("\n🔄 测试重试机制")
    
    client = MockSSEClient("http://localhost:8080")
    
    try:
        # 重置会话
        await client.reset_session()
        
        # 配置错误模拟（30%概率出错）
        await client.configure_llm_error(0.3, ["network", "timeout"])
        await client.configure_llm_delay(0.01)  # 快速测试
        print("✓ 错误模拟已配置")
        
        # 发送消息
        content = "测试重试机制"
        
        print(f"📤 发送消息: {content}")
        
        retry_count = 0
        error_count = 0
        success = False
        
        try:
            async for event in client.send_message(content, "重试测试"):
                data = event["data"]
                
                if data['patch_type'] == 'retry':
                    retry_count += 1
                    print(f"🔄 重试 #{retry_count}: {data['content_delta'].strip()}")
                elif data['patch_type'] == 'error':
                    error_count += 1
                    print(f"❌ 错误: {data['content_delta'].strip()}")
                elif data['patch_type'] == 'complete':
                    success = True
                    print("✅ 完成")
                    break
        except Exception as e:
            print(f"⚠️ 重试过程中出现异常: {e}")
        
        print(f"\n✅ 重试机制测试结果:")
        print(f"   - 重试次数: {retry_count}")
        print(f"   - 错误次数: {error_count}")
        print(f"   - 最终成功: {success}")
        
        # 获取重试统计
        try:
            stats = await client.get_retry_stats()
            print(f"   - 重试统计: {stats}")
        except:
            print("   - 无法获取重试统计")
        
        return True
        
    except Exception as e:
        print(f"❌ 重试机制测试失败: {e}")
        return False
    finally:
        await client.close()


async def test_session_management():
    """测试会话管理"""
    print("\n🔄 测试会话管理")
    
    client = MockSSEClient("http://localhost:8080")
    
    try:
        # 重置会话
        await client.reset_session()
        
        # 发送多条消息
        await client.configure_llm_delay(0.01)
        
        print("📤 发送第一条消息")
        async for event in client.send_message("第一条测试消息", "消息1"):
            if event["data"]["finished"]:
                break
        
        print("📤 发送第二条消息")
        async for event in client.send_message("第二条测试消息", "消息2"):
            if event["data"]["finished"]:
                break
        
        # 获取消息历史
        history = await client.get_message_history()
        print(f"✅ 消息历史包含 {len(history['messages'])} 条消息")
        
        for i, msg in enumerate(history['messages']):
            print(f"   {i+1}. [{msg['role']}] {msg['title']}: {msg['status']}")
        
        # 获取会话状态
        status = await client.get_session_status()
        print(f"✅ 会话状态: {status}")
        
        # 验证基本要求
        assert len(history['messages']) >= 4, "应该有至少4条消息（2条用户+2条助手）"
        
        return True
        
    except Exception as e:
        print(f"❌ 会话管理测试失败: {e}")
        return False
    finally:
        await client.close()


async def test_api_endpoints():
    """测试API接口"""
    print("\n🔄 测试API接口")
    
    client = MockSSEClient("http://localhost:8080")
    
    try:
        # 测试健康检查
        response = await client.client.get("http://localhost:8080/healthz")
        print(f"✅ 健康检查: {response.json()}")
        
        # 测试根路径
        response = await client.client.get("http://localhost:8080/")
        print(f"✅ 根路径: {response.json()}")
        
        # 测试会话状态
        status = await client.get_session_status()
        print(f"✅ 会话状态API: {status}")
        
        # 测试重试统计
        stats = await client.get_retry_stats()
        print(f"✅ 重试统计API: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ API接口测试失败: {e}")
        return False
    finally:
        await client.close()


async def main():
    """主测试函数"""
    print("🚀 开始流式传输技术验证案例集成测试")
    print("=" * 50)
    
    tests = [
        ("基本消息流程", test_basic_message_flow),
        ("API接口功能", test_api_endpoints),
        ("会话管理", test_session_management),
        ("重试机制", test_retry_mechanism),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 执行测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"💥 {test_name} 测试异常: {e}")
            results.append((test_name, False))
        
        # 测试间间隔
        await asyncio.sleep(0.5)
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！流式传输技术验证案例工作正常。")
    else:
        print("⚠️  部分测试失败，需要进一步调试。")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())

