"""
智能体单元测试
测试AutoResearchAgent和UserChatAgent的基础逻辑和提示词效果
"""
import pytest
import asyncio
from unittest.mock import AsyncMock
from typing import Dict, Any

from backend.agents.auto_research_agent import AutoResearchAgent
from backend.agents.user_chat_agent import UserChatAgent
from backend.agents.message_models import Message
from backend.database.DatabaseManager import DatabaseManager
from backend.agents.project_manager import ProjectManager


class TestAutoResearchAgent:
    """测试自动研究智能体"""
    
    @pytest.fixture
    def mock_publish_callback(self):
        """模拟发布回调函数"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_query_database_func(self):
        """模拟数据库查询函数"""
        def query_func(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
            if query_type == "get_problem_detail":
                return {
                    "success": True,
                    "data": {
                        "detail": f"问题 {params['problem_id']} 的详细信息"
                    }
                }
            elif query_type == "get_solution_detail":
                return {
                    "success": True,
                    "data": {
                        "detail": f"解决方案 {params['solution_id']} 的详细信息"
                    }
                }
            elif query_type == "get_compact_text_tree":
                return {
                    "success": True,
                    "data": {
                        "tree_text": "研究树全貌..."
                    }
                }
            elif query_type == "get_current_snapshot":
                return {
                    "success": True,
                    "data": {
                        "id": "test_snapshot",
                        "roots": []
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"未知的查询类型: {query_type}"
                }
        return query_func
    
    @pytest.fixture
    def agent(self, mock_publish_callback, mock_query_database_func):
        return AutoResearchAgent(
            name="test_auto_research", 
            publish_callback=mock_publish_callback,
            query_database_func=mock_query_database_func
        )
    
    def test_agent_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.name == "test_auto_research"
        assert agent.current_problem_id is None
        assert agent.current_solution_id is None
        assert len(agent.problem_queue) == 0
        assert not agent.is_processing
    
    def test_parse_user_input_valid(self, agent):
        """测试有效的用户输入解析"""
        user_input = "问题ID: test_problem_123\n要求: 需要高性能的解决方案"
        problem_id, requirement = agent._parse_user_input(user_input)
        
        assert problem_id == "test_problem_123"
        assert requirement == "需要高性能的解决方案"
    
    def test_parse_user_input_missing_problem_id(self, agent):
        """测试缺少问题ID的用户输入"""
        user_input = "要求: 需要高性能的解决方案"
        
        with pytest.raises(ValueError, match="未找到问题ID"):
            agent._parse_user_input(user_input)
    
    def test_parse_user_input_missing_requirement(self, agent):
        """测试缺少要求的用户输入"""
        user_input = "问题ID: test_problem_123"
        problem_id, requirement = agent._parse_user_input(user_input)
        
        assert problem_id == "test_problem_123"
        assert requirement is None
    
    def test_init_problem_queue(self, agent):
        """测试问题队列初始化"""
        problem_id = "test_problem_123"
        user_requirement = "需要高性能的解决方案"
        
        agent._init_problem_queue(problem_id, user_requirement)
        
        assert len(agent.problem_queue) == 1
        queued_problem = agent.problem_queue[0]
        assert queued_problem[0] == problem_id
        assert queued_problem[1] is None  # 监督者
        assert queued_problem[2] == user_requirement
    
    @pytest.mark.asyncio
    async def test_validate_problem_node(self, agent):
        """测试问题节点验证"""
        problem_id = "test_problem_123"
        problem_node = await agent._validate_problem_node(problem_id)
        
        assert problem_node.id == problem_id
        assert problem_node.type == "problem"
        assert problem_node.problem_type == "implementation"
    
    @pytest.mark.asyncio
    async def test_get_environment_info(self, agent):
        """测试环境信息获取"""
        problem_id = "test_problem_123"
        user_requirement = "需要高性能的解决方案"
        
        env_info = await agent._get_environment_info(problem_id, user_requirement)
        
        assert "current_research_tree_full_text" in env_info
        assert "current_research_problem" in env_info
        assert "expert_solutions_of_all_ancestor_problems" in env_info
        assert "root_problem" in env_info
        assert "other_solutions_of_current_problem" in env_info
        assert env_info["user_prompt"] == user_requirement
    
    @pytest.mark.asyncio
    async def test_prompt_test_method(self, agent, capsys):
        """测试提示词测试方法"""
        problem_id = "test_problem_123"
        user_requirement = "需要高性能的解决方案"
        
        await agent.test_prompt(problem_id, user_requirement)
        
        captured = capsys.readouterr()
        assert "=== 组装好的提示词 ===" in captured.out
        assert "提示词测试完成" in captured.out


class TestUserChatAgent:
    """测试用户提问智能体"""
    
    @pytest.fixture
    def mock_publish_callback(self):
        """模拟发布回调函数"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_query_database_func(self):
        """模拟数据库查询函数"""
        def query_func(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
            if query_type == "get_solution_detail":
                return {
                    "success": True,
                    "data": {
                        "detail": f"解决方案 {params['solution_id']} 的详细信息"
                    }
                }
            elif query_type == "get_compact_text_tree":
                return {
                    "success": True,
                    "data": {
                        "tree_text": "研究树全貌..."
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"未知的查询类型: {query_type}"
                }
        return query_func
    
    @pytest.fixture
    def agent(self, mock_publish_callback, mock_query_database_func):
        return UserChatAgent(
            name="test_user_chat", 
            publish_callback=mock_publish_callback,
            query_database_func=mock_query_database_func
        )
    
    def test_agent_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.name == "test_user_chat"
        assert agent.current_solution_id is None
        assert agent.current_problem_id is None
    
    def test_parse_user_input_valid(self, agent):
        """测试有效的用户输入解析"""
        user_input = "解决方案ID: test_solution_123\n反馈: 这个方案太复杂了，需要简化"
        solution_id, feedback = agent._parse_user_input(user_input)
        
        assert solution_id == "test_solution_123"
        assert feedback == "这个方案太复杂了，需要简化"
    
    def test_parse_user_input_missing_solution_id(self, agent):
        """测试缺少解决方案ID的用户输入"""
        user_input = "反馈: 这个方案太复杂了，需要简化"
        
        with pytest.raises(ValueError, match="未找到解决方案ID"):
            agent._parse_user_input(user_input)
    
    def test_parse_user_input_missing_feedback(self, agent):
        """测试缺少反馈的用户输入"""
        user_input = "解决方案ID: test_solution_123"
        
        with pytest.raises(ValueError, match="未找到反馈内容"):
            agent._parse_user_input(user_input)
    
    @pytest.mark.asyncio
    async def test_validate_solution_node(self, agent):
        """测试解决方案节点验证"""
        solution_id = "test_solution_123"
        solution_node = await agent._validate_solution_node(solution_id)
        
        assert solution_node.id == solution_id
        assert solution_node.type == "solution"
        assert solution_node.title == "测试解决方案"
    
    @pytest.mark.asyncio
    async def test_get_parent_problem_id(self, agent):
        """测试获取父问题ID"""
        solution_id = "test_solution_123"
        parent_id = await agent._get_parent_problem_id(solution_id)
        
        # 由于模拟函数返回None，这里应该断言为None
        assert parent_id is None
    
    @pytest.mark.asyncio
    async def test_get_environment_info_for_analysis(self, agent):
        """测试环境信息获取（用于反馈分析）"""
        feedback = "这个方案太复杂了，需要简化"
        
        env_info = await agent._get_environment_info_for_analysis(feedback)
        
        assert "current_research_tree_full_text" in env_info
        assert "current_solution" in env_info
        assert "user_feedback" in env_info
        assert "visible_messages" in env_info
        assert env_info["user_feedback"] == feedback
    
    @pytest.mark.asyncio
    async def test_prompts_test_method(self, agent, capsys):
        """测试提示词测试方法"""
        solution_id = "test_solution_123"
        feedback = "这个方案太复杂了，需要简化"
        
        await agent.test_prompts(solution_id, feedback)
        
        captured = capsys.readouterr()
        assert "=== 反馈分析提示词 ===" in captured.out
        assert "=== 修改决策提示词 ===" in captured.out
        assert "=== 解决方案修改提示词 ===" in captured.out
        assert "所有提示词测试完成" in captured.out


class TestMessageVisibility:
    """测试消息可见性系统"""
    
    @pytest.fixture
    def project_manager(self):
        """创建项目管理器实例"""
        database_manager = DatabaseManager()
        return ProjectManager(database_manager)
    
    @pytest.fixture
    def sample_messages(self):
        """创建示例消息"""
        from backend.agents.message_models import Message
        
        messages = [
            Message(
                id="msg1",
                role="user",
                status="completed",
                title="全局消息",
                content="这是全局可见的消息",
                visible_node_ids=[]  # 空列表表示全局可见
            ),
            Message(
                id="msg2",
                role="assistant",
                status="completed",
                title="节点特定消息",
                content="这是特定节点可见的消息",
                visible_node_ids=["problem_123"]
            ),
            Message(
                id="msg3",
                role="assistant",
                status="completed",
                title="多节点可见消息",
                content="这是多个节点可见的消息",
                visible_node_ids=["problem_123", "problem_456"]
            )
        ]
        return messages
    
    def test_global_message_visibility(self, project_manager, sample_messages):
        """测试全局消息可见性"""
        # 添加消息到项目管理器
        for msg in sample_messages:
            project_manager.messages[msg.id] = msg
            project_manager.message_order.append(msg.id)
        
        # 测试全局消息对任何节点都可见
        visible_messages = project_manager.get_visible_messages("any_node", "problem")
        
        assert len(visible_messages) >= 1
        global_msg = next((msg for msg in visible_messages if msg["title"] == "全局消息"), None)
        assert global_msg is not None
    
    def test_node_specific_message_visibility(self, project_manager, sample_messages):
        """测试节点特定消息可见性"""
        # 添加消息到项目管理器
        for msg in sample_messages:
            project_manager.messages[msg.id] = msg
            project_manager.message_order.append(msg.id)
        
        # 测试节点特定消息对指定节点可见
        visible_messages = project_manager.get_visible_messages("problem_123", "problem")
        
        assert len(visible_messages) >= 2
        specific_msg = next((msg for msg in visible_messages if msg["title"] == "节点特定消息"), None)
        assert specific_msg is not None
    
    def test_message_visibility_logic(self, project_manager, sample_messages):
        """测试消息可见性逻辑"""
        # 添加消息到项目管理器
        for msg in sample_messages:
            project_manager.messages[msg.id] = msg
            project_manager.message_order.append(msg.id)
        
        # 测试可见性判断
        assert project_manager._is_message_visible(sample_messages[0], "any_node", "problem")  # 全局消息
        assert project_manager._is_message_visible(sample_messages[1], "problem_123", "problem")  # 节点特定消息
        assert not project_manager._is_message_visible(sample_messages[1], "other_node", "problem")  # 其他节点不可见


class TestDatabaseManagerExtensions:
    """测试数据库管理器的扩展功能"""
    
    @pytest.fixture
    def database_manager(self):
        """创建数据库管理器实例"""
        return DatabaseManager()
    
    def test_find_node_by_title(self, database_manager):
        """测试根据标题查找节点"""
        # 创建测试数据
        from backend.database.schemas.research_tree import CreateRootProblemRequest
        
        request = CreateRootProblemRequest(
            title="测试问题",
            significance="测试意义",
            criteria="测试标准"
        )
        
        snapshot = database_manager.add_root_problem(request)
        problem_id = snapshot.roots[0].id
        
        # 测试查找
        found_node = database_manager.find_node_by_title("测试问题")
        assert found_node is not None
        assert found_node.id == problem_id
        assert found_node.title == "测试问题"
    
    def test_find_problem_by_title(self, database_manager):
        """测试根据标题查找问题节点"""
        # 创建测试数据
        from backend.database.schemas.research_tree import CreateRootProblemRequest
        
        request = CreateRootProblemRequest(
            title="测试问题",
            significance="测试意义",
            criteria="测试标准"
        )
        
        snapshot = database_manager.add_root_problem(request)
        problem_id = snapshot.roots[0].id
        
        # 测试查找
        found_problem = database_manager.find_problem_by_title("测试问题")
        assert found_problem is not None
        assert found_problem.id == problem_id
        assert found_problem.title == "测试问题"
        assert found_problem.type == "problem"
    
    def test_find_solution_by_title(self, database_manager):
        """测试根据标题查找解决方案节点"""
        # 创建测试数据
        from backend.database.schemas.research_tree import CreateRootProblemRequest, CreateSolutionRequest
        
        # 先创建问题
        problem_request = CreateRootProblemRequest(
            title="测试问题",
            significance="测试意义",
            criteria="测试标准"
        )
        
        snapshot = database_manager.add_root_problem(problem_request)
        problem_id = snapshot.roots[0].id
        
        # 再创建解决方案
        solution_request = CreateSolutionRequest(
            title="测试解决方案",
            top_level_thoughts="测试思考",
            plan_justification="测试论证"
        )
        
        snapshot = database_manager.create_solution(problem_id, solution_request)
        
        # 测试查找
        found_solution = database_manager.find_solution_by_title("测试解决方案")
        assert found_solution is not None
        assert found_solution.title == "测试解决方案"
        assert found_solution.type == "solution"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
