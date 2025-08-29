"""
重试机制测试
测试整个生成器过程的重试包装、消息状态回溯和重新生成
"""
import pytest
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.session_manager import SessionManager
from core.agent_coroutine import AgentCoroutine
from core.generator_retry import AgentGeneratorRetry
from core.llm_client import NetworkError, TimeoutError
from models.message import Patch
from utils.logger import logger


@pytest.fixture
def session_manager():
    """会话管理器fixture"""
    mgr = SessionManager()
    yield mgr
    mgr.reset()


@pytest.fixture
def retry_wrapper():
    """重试包装器fixture"""
    wrapper = AgentGeneratorRetry(max_retries=2, base_delay=0.1, max_delay=1.0)
    yield wrapper
    wrapper.reset_stats()


@pytest.mark.asyncio
class TestRetryMechanism:
    """重试机制测试类"""
    
    async def test_successful_generation_no_retry(self, session_manager, retry_wrapper):
        """测试成功生成（无需重试）"""
        print("\n=== 测试成功生成（无需重试）===")
        
        # 创建助手消息
        message = session_manager.create_message("assistant", "测试回复")
        
        async def successful_generator(content, message_id):
            """成功的生成器（不抛出异常）"""
            print("  🔄 开始生成...")
            
            yield Patch(
                message_id=message_id,
                patch_type="thinking",
                thinking_delta="正在思考...\n",
                finished=False
            )
            
            yield Patch(
                message_id=message_id,
                patch_type="content",
                content_delta="这是一个成功的回复。",
                finished=False
            )
            
            yield Patch(
                message_id=message_id,
                patch_type="complete",
                finished=True
            )
            
            print("  ✅ 生成完成")
        
        # 执行生成器（使用重试包装器）
        patches = []
        async for patch in retry_wrapper.execute_with_retry(
            successful_generator,
            session_manager,
            "测试内容",
            message.id
        ):
            patches.append(patch)
            print(f"  📦 收到patch: {patch.patch_type}")
        
        # 验证结果
        assert len(patches) == 3
        assert patches[0].patch_type == "thinking"
        assert patches[1].patch_type == "content"
        assert patches[2].patch_type == "complete"
        
        # 验证统计信息
        stats = retry_wrapper.get_retry_stats()
        print(f"✓ 重试统计: {stats}")
        assert stats["total_attempts"] == 1
        assert stats["successful_attempts"] == 1
        assert stats["failed_attempts"] == 0
        
        print("✓ 成功生成验证通过")
    
    async def test_retry_on_network_error(self, session_manager, retry_wrapper):
        """测试网络错误重试"""
        print("\n=== 测试网络错误重试 ===")
        
        # 创建助手消息
        message = session_manager.create_message("assistant", "测试回复")
        
        attempt_count = 0
        
        async def failing_then_success_generator(content, message_id):
            """第一次失败，第二次成功的生成器"""
            nonlocal attempt_count
            attempt_count += 1
            
            print(f"  🔄 第{attempt_count}次尝试开始...")
            
            if attempt_count == 1:
                # 第一次尝试：模拟网络错误
                yield Patch(
                    message_id=message_id,
                    patch_type="thinking",
                    thinking_delta="开始思考...\n",
                    finished=False
                )
                
                print("  ❌ 模拟网络错误")
                raise NetworkError("模拟网络连接失败")
            else:
                # 第二次尝试：成功
                yield Patch(
                    message_id=message_id,
                    patch_type="thinking",
                    thinking_delta="重新开始思考...\n",
                    finished=False
                )
                
                yield Patch(
                    message_id=message_id,
                    patch_type="content",
                    content_delta="重试后的成功回复。",
                    finished=False
                )
                
                yield Patch(
                    message_id=message_id,
                    patch_type="complete",
                    finished=True
                )
                
                print("  ✅ 重试成功")
        
        # 执行生成器（使用重试包装器）
        patches = []
        async for patch in retry_wrapper.execute_with_retry(
            failing_then_success_generator,
            session_manager,
            "测试内容",
            message.id
        ):
            patches.append(patch)
            print(f"  📦 收到patch: {patch.patch_type}")
            if patch.patch_type == "retry":
                print(f"     重试通知: {patch.content_delta.strip()}")
        
        # 验证重试过程
        retry_patches = [p for p in patches if p.patch_type == "retry"]
        success_patches = [p for p in patches if p.patch_type in ["thinking", "content", "complete"]]
        
        print(f"✓ 重试patch数量: {len(retry_patches)}")
        print(f"✓ 成功patch数量: {len(success_patches)}")
        
        assert len(retry_patches) == 1  # 一次重试通知
        assert len(success_patches) == 4  # 第一次失败的thinking + 第二次成功的patches
        
        # 验证统计信息
        stats = retry_wrapper.get_retry_stats()
        print(f"✓ 重试统计: {stats}")
        assert stats["total_attempts"] == 2  # 总尝试次数
        assert stats["successful_attempts"] == 1  # 最终成功次数
        assert stats["failed_attempts"] == 0  # 最终失败次数（重试成功了所以是0）
        
        print("✓ 网络错误重试验证通过")
    
    async def test_max_retries_exceeded(self, session_manager, retry_wrapper):
        """测试超过最大重试次数"""
        print("\n=== 测试超过最大重试次数 ===")
        
        # 创建助手消息
        message = session_manager.create_message("assistant", "测试回复")
        
        attempt_count = 0
        
        async def always_failing_generator(content, message_id):
            """总是失败的生成器"""
            nonlocal attempt_count
            attempt_count += 1
            
            print(f"  🔄 第{attempt_count}次尝试（总是失败）...")
            
            yield Patch(
                message_id=message_id,
                patch_type="thinking",
                thinking_delta=f"第{attempt_count}次思考...\n",
                finished=False
            )
            
            print(f"  ❌ 第{attempt_count}次失败")
            # 使用我们自定义的TimeoutError而不是内置的
            from core.llm_client import TimeoutError as LLMTimeoutError
            raise LLMTimeoutError(f"第{attempt_count}次模拟超时")
        
        # 执行生成器，预期最终失败
        patches = []
        from core.llm_client import TimeoutError as LLMTimeoutError
        with pytest.raises(LLMTimeoutError):
            async for patch in retry_wrapper.execute_with_retry(
                always_failing_generator,
                session_manager,
                "测试内容",
                message.id
            ):
                patches.append(patch)
                print(f"  📦 收到patch: {patch.patch_type}")
                if patch.patch_type == "retry":
                    print(f"     重试通知: {patch.content_delta.strip()}")
                elif patch.patch_type == "error":
                    print(f"     错误通知: {patch.content_delta.strip()}")
        
        # 验证重试次数
        retry_patches = [p for p in patches if p.patch_type == "retry"]
        error_patches = [p for p in patches if p.patch_type == "error"]
        
        print(f"✓ 重试patch数量: {len(retry_patches)}")
        print(f"✓ 错误patch数量: {len(error_patches)}")
        print(f"✓ 实际尝试次数: {attempt_count}")
        
        assert len(retry_patches) == retry_wrapper.max_retries  # 重试次数等于最大重试次数
        assert len(error_patches) == 1  # 最终失败通知
        assert attempt_count == retry_wrapper.max_retries + 1  # 总尝试次数 = 最大重试次数 + 1
        
        # 验证统计信息
        stats = retry_wrapper.get_retry_stats()
        print(f"✓ 重试统计: {stats}")
        assert stats["failed_attempts"] == 1  # 最终失败
        
        print("✓ 超过最大重试次数验证通过")
    
    async def test_non_retryable_error(self, session_manager, retry_wrapper):
        """测试不可重试错误"""
        print("\n=== 测试不可重试错误 ===")
        
        # 创建助手消息
        message = session_manager.create_message("assistant", "测试回复")
        
        async def non_retryable_error_generator(content, message_id):
            """抛出不可重试错误的生成器"""
            print("  🔄 开始生成...")
            
            yield Patch(
                message_id=message_id,
                patch_type="thinking",
                thinking_delta="开始思考...\n",
                finished=False
            )
            
            print("  ❌ 抛出不可重试错误")
            raise ValueError("这是一个不可重试的业务逻辑错误")
        
        # 执行生成器，预期立即失败
        patches = []
        with pytest.raises(ValueError):
            async for patch in retry_wrapper.execute_with_retry(
                non_retryable_error_generator,
                session_manager,
                "测试内容",
                message.id
            ):
                patches.append(patch)
                print(f"  📦 收到patch: {patch.patch_type}")
                if patch.patch_type == "error":
                    print(f"     错误通知: {patch.content_delta.strip()}")
        
        # 验证没有重试
        retry_patches = [p for p in patches if p.patch_type == "retry"]
        error_patches = [p for p in patches if p.patch_type == "error"]
        
        print(f"✓ 重试patch数量: {len(retry_patches)}")
        print(f"✓ 错误patch数量: {len(error_patches)}")
        
        assert len(retry_patches) == 0  # 不可重试错误不应该有重试
        assert len(error_patches) == 1  # 应该有错误通知
        
        # 验证统计信息
        stats = retry_wrapper.get_retry_stats()
        print(f"✓ 重试统计: {stats}")
        assert stats["total_attempts"] == 1
        assert stats["failed_attempts"] == 1
        
        print("✓ 不可重试错误验证通过")
    
    async def test_message_rollback(self, session_manager, retry_wrapper):
        """测试消息状态回溯"""
        print("\n=== 测试消息状态回溯 ===")
        
        # 创建助手消息
        message = session_manager.create_message("assistant", "测试回复")
        
        attempt_count = 0
        
        async def partial_failure_generator(content, message_id):
            """部分完成后失败的生成器"""
            nonlocal attempt_count
            attempt_count += 1
            
            print(f"  🔄 第{attempt_count}次尝试开始...")
            
            # 先生成一些内容
            yield Patch(
                message_id=message_id,
                patch_type="thinking",
                thinking_delta=f"第{attempt_count}次思考过程...\n",
                finished=False
            )
            
            yield Patch(
                message_id=message_id,
                patch_type="content",
                content_delta=f"第{attempt_count}次内容开始...",
                finished=False
            )
            
            if attempt_count == 1:
                print("  ❌ 在生成过程中失败")
                raise NetworkError("生成过程中的网络错误")
            else:
                # 第二次成功完成
                yield Patch(
                    message_id=message_id,
                    patch_type="content",
                    content_delta="重试后完成内容。",
                    finished=False
                )
                
                yield Patch(
                    message_id=message_id,
                    patch_type="complete",
                    finished=True
                )
                print("  ✅ 重试后成功完成")
        
        # 记录消息的初始状态
        initial_thinking = message.thinking
        initial_content = message.content
        
        print(f"✓ 初始状态 - 思考: '{initial_thinking}', 内容: '{initial_content}'")
        
        # 执行生成器
        patches = []
        async for patch in retry_wrapper.execute_with_retry(
            partial_failure_generator,
            session_manager,
            "测试内容",
            message.id
        ):
            patches.append(patch)
            # 应用patch到消息
            session_manager.update_message(message.id, patch)
            
            print(f"  📦 应用patch: {patch.patch_type}")
            if patch.patch_type == "retry":
                print(f"     重试后消息状态 - 思考: '{message.thinking}', 内容: '{message.content}'")
        
        # 验证最终状态
        final_message = session_manager.get_message(message.id)
        print(f"✓ 最终状态 - 思考: '{final_message.thinking}'")
        print(f"✓ 最终状态 - 内容: '{final_message.content}'")
        
        # 验证消息状态被正确回溯和重建
        assert "第2次思考过程" in final_message.thinking
        assert "重试后完成内容" in final_message.content
        assert final_message.status == "completed"
        
        print("✓ 消息状态回溯验证通过")
