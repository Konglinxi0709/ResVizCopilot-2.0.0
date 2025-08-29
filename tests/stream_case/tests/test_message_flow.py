"""
消息流程测试
测试用户消息创建和助手消息生成，验证Patch的增量更新和替换更新逻辑
"""
import pytest
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.session_manager import SessionManager
from core.agent_coroutine import AgentCoroutine
from models.message import Message, Patch
from utils.logger import logger


@pytest.fixture
def session_manager():
    """会话管理器fixture"""
    mgr = SessionManager()
    yield mgr
    mgr.reset()


@pytest.fixture
def agent_coroutine(session_manager):
    """智能体协程fixture"""
    agent = AgentCoroutine(session_manager)
    yield agent


@pytest.mark.asyncio
class TestMessageFlow:
    """消息流程测试类"""
    
    async def test_create_user_message(self, session_manager):
        """测试创建用户消息"""
        print("\n=== 测试创建用户消息 ===")
        
        # 创建用户消息
        message = session_manager.create_message("user", "测试用户消息")
        message.content = "这是一个测试消息"
        message.status = "completed"
        
        print(f"✓ 创建用户消息: {message.id}")
        print(f"  - 角色: {message.role}")
        print(f"  - 状态: {message.status}")
        print(f"  - 标题: {message.title}")
        print(f"  - 内容: {message.content}")
        
        # 验证消息属性
        assert message.role == "user"
        assert message.status == "completed"
        assert message.title == "测试用户消息"
        assert message.content == "这是一个测试消息"
        assert message.id in session_manager.messages
        
        print("✓ 用户消息创建验证通过")
    
    async def test_create_assistant_message(self, session_manager):
        """测试创建助手消息"""
        print("\n=== 测试创建助手消息 ===")
        
        # 创建助手消息
        message = session_manager.create_message("assistant", "智能体回复")
        
        print(f"✓ 创建助手消息: {message.id}")
        print(f"  - 角色: {message.role}")
        print(f"  - 状态: {message.status}")
        print(f"  - 标题: {message.title}")
        
        # 验证消息属性
        assert message.role == "assistant"
        assert message.status == "generating"  # 助手消息初始状态为generating
        assert message.title == "智能体回复"
        assert message.content == ""  # 内容初始为空
        
        print("✓ 助手消息创建验证通过")
    
    async def test_patch_incremental_update(self, session_manager):
        """测试Patch增量更新"""
        print("\n=== 测试Patch增量更新 ===")
        
        # 创建助手消息
        message = session_manager.create_message("assistant", "测试回复")
        
        # 创建思考patch
        thinking_patch = Patch(
            message_id=message.id,
            patch_type="thinking",
            thinking_delta="我正在思考这个问题...\n",
            finished=False
        )
        
        print(f"✓ 应用思考patch: {thinking_patch.thinking_delta.strip()}")
        thinking_patch.apply_to_message(message)
        assert message.thinking == "我正在思考这个问题...\n"
        
        # 创建内容patch
        content_patch = Patch(
            message_id=message.id,
            patch_type="content",
            content_delta="根据你的问题，",
            finished=False
        )
        
        print(f"✓ 应用内容patch: {content_patch.content_delta}")
        content_patch.apply_to_message(message)
        assert message.content == "根据你的问题，"
        
        # 继续添加内容
        content_patch2 = Patch(
            message_id=message.id,
            patch_type="content",
            content_delta="我认为应该这样解决...",
            finished=False
        )
        
        print(f"✓ 应用第二个内容patch: {content_patch2.content_delta}")
        content_patch2.apply_to_message(message)
        assert message.content == "根据你的问题，我认为应该这样解决..."
        
        print(f"✓ 最终消息内容: {message.content}")
        print("✓ Patch增量更新验证通过")
    
    async def test_patch_replacement_update(self, session_manager):
        """测试Patch替换更新"""
        print("\n=== 测试Patch替换更新 ===")
        
        # 创建助手消息
        message = session_manager.create_message("assistant", "测试回复")
        
        # 应用替换更新patch
        replace_patch = Patch(
            message_id=message.id,
            patch_type="action",
            title="新标题",
            action_title="create_problem",
            action_params={"title": "新问题", "type": "research"},
            snapshot_id="snapshot_123",
            finished=False
        )
        
        print(f"✓ 应用替换patch:")
        print(f"  - 新标题: {replace_patch.title}")
        print(f"  - 行动标题: {replace_patch.action_title}")
        print(f"  - 行动参数: {replace_patch.action_params}")
        print(f"  - 快照ID: {replace_patch.snapshot_id}")
        
        replace_patch.apply_to_message(message)
        
        # 验证替换更新
        assert message.title == "新标题"
        assert message.action_title == "create_problem"
        assert message.action_params == {"title": "新问题", "type": "research"}
        assert message.snapshot_id == "snapshot_123"
        
        print("✓ Patch替换更新验证通过")
    
    async def test_message_completion(self, session_manager):
        """测试消息完成状态转换"""
        print("\n=== 测试消息完成状态转换 ===")
        
        # 创建助手消息
        message = session_manager.create_message("assistant", "测试回复")
        initial_status = message.status
        
        print(f"✓ 初始状态: {initial_status}")
        
        # 应用完成patch
        complete_patch = Patch(
            message_id=message.id,
            patch_type="complete",
            finished=True
        )
        
        complete_patch.apply_to_message(message)
        
        print(f"✓ 完成后状态: {message.status}")
        
        # 验证状态转换
        assert initial_status == "generating"
        assert message.status == "completed"
        
        print("✓ 消息状态转换验证通过")
    
    async def test_message_history(self, session_manager):
        """测试消息历史管理"""
        print("\n=== 测试消息历史管理 ===")
        
        # 创建多条消息
        user_msg = session_manager.create_message("user", "用户消息1")
        user_msg.content = "第一条用户消息"
        user_msg.status = "completed"
        
        assistant_msg = session_manager.create_message("assistant", "智能体回复1")
        assistant_msg.content = "第一条智能体回复"
        assistant_msg.status = "completed"
        
        user_msg2 = session_manager.create_message("user", "用户消息2")
        user_msg2.content = "第二条用户消息"
        user_msg2.status = "completed"
        
        print(f"✓ 创建了3条消息")
        
        # 获取消息历史
        history = session_manager.get_message_history()
        
        print(f"✓ 消息历史数量: {len(history)}")
        for i, msg in enumerate(history):
            print(f"  {i+1}. [{msg.role}] {msg.title}: {msg.content}")
        
        # 验证历史顺序
        assert len(history) == 3
        assert history[0].id == user_msg.id
        assert history[1].id == assistant_msg.id
        assert history[2].id == user_msg2.id
        
        print("✓ 消息历史管理验证通过")
    
    async def test_incomplete_message_detection(self, session_manager):
        """测试未完成消息检测"""
        print("\n=== 测试未完成消息检测 ===")
        
        # 创建完成的消息
        completed_msg = session_manager.create_message("user", "完成的消息")
        completed_msg.status = "completed"
        
        # 创建未完成的消息
        incomplete_msg = session_manager.create_message("assistant", "未完成的消息")
        # assistant消息默认为generating状态
        
        print(f"✓ 完成消息: {completed_msg.title} - {completed_msg.status}")
        print(f"✓ 未完成消息: {incomplete_msg.title} - {incomplete_msg.status}")
        
        # 检测未完成消息
        found_incomplete = session_manager.get_incomplete_message()
        
        print(f"✓ 检测到未完成消息: {found_incomplete.title if found_incomplete else 'None'}")
        
        # 验证检测结果
        assert found_incomplete is not None
        assert found_incomplete.id == incomplete_msg.id
        assert found_incomplete.status == "generating"
        
        print("✓ 未完成消息检测验证通过")
