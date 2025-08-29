"""
消息系统测试
测试Message、Patch和ProjectManager的功能
"""
import pytest
import asyncio
from typing import Dict, Any

from backend.agents.message_models import Message, Patch, FrontendPatch
from backend.agents.project_manager import ProjectManager
from backend.database.DatabaseManager import DatabaseManager


class TestMessageModels:
    """消息模型测试类"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        print("\n=== 开始消息模型测试 ===")
    
    def test_message_creation(self):
        """测试消息创建"""
        message = Message(
            role="user",
            status="completed",
            title="测试消息",
            content="这是一条测试消息"
        )
        
        print(f"创建的消息: {message}")
        print(f"消息ID: {message.id}")
        print(f"角色: {message.role}")
        print(f"状态: {message.status}")
        
        assert message.role == "user"
        assert message.status == "completed"
        assert message.title == "测试消息"
        assert message.content == "这是一条测试消息"
        assert message.id is not None
        print("✅ 消息创建测试通过")
    
    def test_patch_application(self):
        """测试补丁应用"""
        message = Message(
            role="assistant",
            status="generating",
            title="",
            content="",
            thinking=""
        )
        
        print(f"初始消息: {message}")
        
        # 应用思考增量补丁
        thinking_patch = Patch(
            message_id=message.id,
            thinking_delta="我在思考这个问题...",
            title="智能体回复"
        )
        
        thinking_patch.apply_to_message(message)
        print(f"应用思考补丁后: thinking='{message.thinking}', title='{message.title}'")
        
        # 应用内容增量补丁
        content_patch = Patch(
            message_id=message.id,
            content_delta="这是我的回答",
            finished=True
        )
        
        content_patch.apply_to_message(message)
        print(f"应用内容补丁后: content='{message.content}', status='{message.status}'")
        
        assert message.thinking == "我在思考这个问题..."
        assert message.title == "智能体回复"
        assert message.content == "这是我的回答"
        assert message.status == "completed"
        print("✅ 补丁应用测试通过")
    
    def test_frontend_patch_creation(self):
        """测试前端补丁创建"""
        patch = Patch(
            message_id="test_id",
            content_delta="测试内容",
            snapshot_id="snapshot_123"
        )
        
        snapshot_obj = {
            "id": "snapshot_123",
            "data": {"test": "data"},
            "summary": "测试快照"
        }
        
        frontend_patch = FrontendPatch.from_patch(patch, snapshot_obj)
        
        print(f"原始补丁: {patch}")
        print(f"前端补丁: {frontend_patch}")
        print(f"快照对象: {frontend_patch.snapshot}")
        
        assert frontend_patch.message_id == "test_id"
        assert frontend_patch.content_delta == "测试内容"
        assert frontend_patch.snapshot_id == "snapshot_123"
        assert frontend_patch.snapshot == snapshot_obj
        print("✅ 前端补丁创建测试通过")


class TestProjectManager:
    """项目管理器测试类"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.db_manager = DatabaseManager()
        self.project_manager = ProjectManager(self.db_manager)
        print("\n=== 开始项目管理器测试 ===")
    
    @pytest.mark.asyncio
    async def test_publish_patch_create_message(self):
        """测试发布补丁创建消息"""
        patch = Patch(
            message_id=None,  # 创建新消息
            role="user",  # 明确指定role
            title="测试消息",
            content_delta="测试内容",
            finished=True
        )
        
        print(f"发布补丁: {patch}")
        message_id = await self.project_manager.publish_patch(patch)
        print(f"创建的消息ID: {message_id}")
        
        # 验证消息创建
        message = self.project_manager.get_message(message_id)
        print(f"获取的消息: {message}")
        
        assert message is not None
        assert message.title == "测试消息"
        assert message.content == "测试内容"
        assert message.status == "completed"
        print("✅ 发布补丁创建消息测试通过")
    
    @pytest.mark.asyncio
    async def test_publish_patch_update_message(self):
        """测试发布补丁更新消息"""
        # 先创建一条消息
        create_patch = Patch(
            message_id=None,
            role="user",  # 明确指定role
            title="原始消息",
            content_delta="原始内容"
        )
        
        message_id = await self.project_manager.publish_patch(create_patch)
        print(f"创建消息ID: {message_id}")
        
        # 更新消息
        update_patch = Patch(
            message_id=message_id,
            content_delta="追加内容",
            finished=True
        )
        
        await self.project_manager.publish_patch(update_patch)
        
        # 验证更新
        message = self.project_manager.get_message(message_id)
        print(f"更新后的消息: {message}")
        
        assert message.content == "原始内容追加内容"
        assert message.status == "completed"
        print("✅ 发布补丁更新消息测试通过")
    
    @pytest.mark.asyncio
    async def test_message_history(self):
        """测试消息历史"""
        # 创建多条消息
        for i in range(3):
            patch = Patch(
                message_id=None,
                role="user",  # 明确指定role
                title=f"消息{i+1}",
                content_delta=f"内容{i+1}",
                finished=True
            )
            await self.project_manager.publish_patch(patch)
        
        history = self.project_manager.get_message_history()
        print(f"消息历史: {len(history)}条消息")
        
        for i, msg in enumerate(history):
            print(f"  消息{i+1}: {msg.title} - {msg.content}")
        
        assert len(history) == 3
        assert history[0].title == "消息1"
        assert history[1].title == "消息2" 
        assert history[2].title == "消息3"
        print("✅ 消息历史测试通过")
    
    @pytest.mark.asyncio
    async def test_incomplete_message(self):
        """测试未完成消息检测"""
        # 创建一条未完成的消息
        patch = Patch(
            message_id=None,
            role="assistant",  # 明确指定为助手消息
            title="生成中的消息",
            thinking_delta="正在思考...",
            finished=False  # 明确设置为False
        )
        
        message_id = await self.project_manager.publish_patch(patch)
        print(f"创建生成中的消息ID: {message_id}")
        
        # 检查未完成消息
        incomplete_msg = self.project_manager.get_incomplete_message()
        print(f"检测到未完成消息: {incomplete_msg}")
        
        assert incomplete_msg is not None
        assert incomplete_msg.id == message_id
        assert incomplete_msg.status == "generating"
        print("✅ 未完成消息检测测试通过")
    
    def test_database_action_execution(self):
        """测试数据库操作执行"""
        # 测试创建根问题
        params = {
            "title": "测试问题",
            "significance": "这是一个测试问题",
            "criteria": "测试标准",
            "problem_type": "implementation"
        }
        
        print(f"执行数据库操作: create_root_problem, 参数: {params}")
        result = self.project_manager.execute_database_action("create_root_problem", params)
        print(f"执行结果: {result}")
        
        assert result["success"] is True
        assert "成功创建根问题" in result["message"]
        assert result["snapshot_id"] is not None
        print("✅ 数据库操作执行测试通过")
    
    def test_project_status(self):
        """测试项目状态获取"""
        status = self.project_manager.get_status()
        print(f"项目状态: {status}")
        
        assert "message_count" in status
        assert "current_message_id" in status
        assert "is_generating" in status
        assert "queue_size" in status
        assert "registered_agents" in status
        assert "database_state" in status
        
        print("✅ 项目状态获取测试通过")


if __name__ == "__main__":
    # 运行消息模型测试
    print("🧪 开始运行消息系统测试套件")
    
    try:
        # 测试消息模型
        msg_test = TestMessageModels()
        msg_test.setup_method()
        msg_test.test_message_creation()
        print()
        
        msg_test.setup_method()
        msg_test.test_patch_application()
        print()
        
        msg_test.setup_method()
        msg_test.test_frontend_patch_creation()
        print()
        
        # 测试项目管理器
        pm_test = TestProjectManager()
        
        # 运行异步测试
        async def run_async_tests():
            pm_test.setup_method()
            await pm_test.test_publish_patch_create_message()
            print()
            
            pm_test.setup_method()
            await pm_test.test_publish_patch_update_message()
            print()
            
            pm_test.setup_method()
            await pm_test.test_message_history()
            print()
            
            pm_test.setup_method()
            await pm_test.test_incomplete_message()
            print()
        
        asyncio.run(run_async_tests())
        
        # 运行同步测试
        pm_test.setup_method()
        pm_test.test_database_action_execution()
        print()
        
        pm_test.setup_method()
        pm_test.test_project_status()
        
        print("\n🎉 所有消息系统测试都通过了！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise
