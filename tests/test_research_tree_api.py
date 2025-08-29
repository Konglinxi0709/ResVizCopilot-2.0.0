from fastapi.testclient import TestClient

from backend.main import app
from backend.database.DatabaseManager import DatabaseManager


client = TestClient(app)


def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200


async def test_research_tree_operations():
    """测试研究树基本操作"""
    print("\n=== 开始测试研究树基本操作 ===")
    
    # 创建数据库管理器实例
    db = DatabaseManager()
    
    # 测试添加根问题
    from backend.database.schemas.research_tree import CreateRootProblemRequest
    root_req = CreateRootProblemRequest(
        title="测试根问题",
        significance="测试重要性",
        criteria="测试标准"
    )
    snap1 = await db.add_root_problem(root_req)
    print(f"[DB ADD ROOT] 添加根问题后快照ID: {snap1.id}")
    assert len(snap1.roots) == 1
    assert snap1.roots[0].title == "测试根问题"
    
    # 测试创建带子问题的解决方案
    from backend.database.schemas.research_tree import CreateSolutionRequest, CreateProblemRequest
    child_problem = CreateProblemRequest(
        title="子问题1",
        significance="子问题重要性",
        criteria="子问题标准",
        problem_type="implementation"
    )
    sol_req = CreateSolutionRequest(
        title="测试方案",
        top_level_thoughts="顶层思考",
        plan_justification="方案依据",
        finishing_task="收尾任务",
        children=[child_problem]
    )
    snap2 = await db.create_solution(snap1.roots[0].id, sol_req)
    print(f"[DB CREATE SOL] 创建方案后快照ID: {snap2.id}")
    assert len(snap2.roots[0].children) == 1
    assert snap2.roots[0].children[0].title == "测试方案"
    assert len(snap2.roots[0].children[0].children) == 1
    assert snap2.roots[0].children[0].children[0].title == "子问题1"
    
    # 测试复用已有问题节点
    reuse_problem = CreateProblemRequest(
        id=snap2.roots[0].children[0].children[0].id,  # 复用刚创建的子问题
        title="新标题",  # 这个标题应该被忽略
        significance="新重要性",  # 这个也应该被忽略
        criteria="新标准",
        problem_type="implementation"
    )
    sol_req2 = CreateSolutionRequest(
        title="测试方案2",
        children=[reuse_problem]
    )
    snap3 = await db.create_solution(snap1.roots[0].id, sol_req2)
    print(f"[DB REUSE PROBLEM] 复用问题后快照ID: {snap3.id}")
    # 验证复用的节点保持了原来的标题
    reused_node = snap3.roots[0].children[1].children[0]
    assert reused_node.title == "子问题1"  # 保持原标题，不是"新标题"
    
    # 测试条件问题不能有解决方案
    from backend.database.schemas.research_tree import ProblemType
    conditional_root = CreateRootProblemRequest(
        title="条件问题",
        significance="条件重要性",
        criteria="条件标准",
        problem_type="implementation"  # 先创建为implementation
    )
    snap4 = await db.add_root_problem(conditional_root)
    # 更新为conditional
    from backend.database.schemas.research_tree import UpdateProblemRequest
    update_req = UpdateProblemRequest(problem_type="conditional")  # 使用字符串值
    try:
        await db.update_root_problem(snap4.roots[1].id, update_req)
        # 尝试为条件问题创建解决方案
        try:
            await db.create_solution(snap4.roots[1].id, CreateSolutionRequest(title="测试"))
            assert False, "条件问题不应该能创建解决方案"
        except ValueError as e:
            print(f"[DB CONDITIONAL ERROR] 正确捕获错误: {e}")
            assert "Conditional problem cannot have solutions" in str(e)
    except ValueError as e:
        print(f"[DB ROOT CONDITIONAL ERROR] 根问题不能改为conditional: {e}")
        assert "Root problem cannot be CONDITIONAL" in str(e)
    
    # 测试文本树生成
    text_tree = db.get_compact_text_tree()
    print(f"[DB TEXT TREE] 文本树:\n{text_tree}")
    assert "测试根问题" in text_tree
    assert "测试方案" in text_tree
    assert "子问题1" in text_tree
    
    # 测试相关方案查找
    related = db.get_related_solutions(snap2.roots[0].children[0].id)
    print(f"[DB RELATED] 相关方案: ancestors={related.ancestors}, descendants={related.descendants}, siblings={related.siblings}")
    
    # 测试方案详情XML格式
    detail = db.get_solution_detail(snap2.roots[0].children[0].id)
    print(f"[DB SOLUTION DETAIL] XML格式详情:\n{detail}")
    assert "<name>" in detail
    assert "<implementation_plan>" in detail
    assert "<step type=implementation>" in detail


async def test_snapshot_immutability():
    """测试快照不可变性"""
    print("\n=== 开始测试快照不可变性 ===")
    
    db = DatabaseManager()
    
    # 记录初始快照
    initial_snap = db.get_current_snapshot()
    initial_id = initial_snap.id
    print(f"[IMMUTABILITY] 初始快照ID: {initial_id}")
    
    # 执行一系列操作
    from backend.database.schemas.research_tree import CreateRootProblemRequest
    root_req = CreateRootProblemRequest(
        title="测试问题",
        significance="重要性",
        criteria="标准",
        problem_type="implementation"
    )
    
    snap1 = await db.add_root_problem(root_req)
    snap1_id = snap1.id
    print(f"[IMMUTABILITY] 操作1后快照ID: {snap1_id}")
    assert snap1_id != initial_id
    
    # 验证初始快照仍然存在且未改变
    assert initial_snap.id == initial_id
    assert len(initial_snap.roots) == 0  # 初始快照应该仍然是空的
    
    # 继续操作
    from backend.database.schemas.research_tree import CreateSolutionRequest
    sol_req = CreateSolutionRequest(title="测试方案")
    snap2 = await db.create_solution(snap1.roots[0].id, sol_req)
    snap2_id = snap2.id
    print(f"[IMMUTABILITY] 操作2后快照ID: {snap2_id}")
    assert snap2_id != snap1_id
    assert snap2_id != initial_id
    
    # 验证所有历史快照都保持不变
    assert initial_snap.id == initial_id
    assert len(initial_snap.roots) == 0
    assert snap1.id == snap1_id
    assert len(snap1.roots) == 1
    assert len(snap1.roots[0].children) == 0  # snap1中还没有方案
    
    print(f"[IMMUTABILITY] 验证完成：所有历史快照都保持不可变")


async def test_error_handling():
    """测试错误处理"""
    print("\n=== 开始测试错误处理 ===")
    
    db = DatabaseManager()
    
    # 测试查找不存在的节点
    try:
        db._find_node_in([], "non-existent")
        print("[ERROR HANDLING] 空列表中查找不存在的节点: 正确返回None")
    except Exception as e:
        assert False, f"不应该抛出异常: {e}"
    
    # 测试删除不存在的根问题
    try:
        await db.delete_root_problem("non-existent")
        assert False, "应该抛出KeyError"
    except KeyError as e:
        print(f"[ERROR HANDLING] 删除不存在的根问题: 正确抛出KeyError: {e}")
    
    # 测试删除不存在的方案
    try:
        await db.delete_solution("non-existent")
        assert False, "应该抛出KeyError"
    except KeyError as e:
        print(f"[ERROR HANDLING] 删除不存在的方案: 正确抛出KeyError: {e}")
    
    # 测试设置不属于该问题的方案
    # 先创建一个问题
    from backend.database.schemas.research_tree import CreateRootProblemRequest
    root_req = CreateRootProblemRequest(
        title="测试问题",
        significance="重要性",
        criteria="标准",
        problem_type="implementation"
    )
    snap = await db.add_root_problem(root_req)
    
    try:
        await db.set_selected_solution(snap.roots[0].id, "non-existent-solution")
        assert False, "应该抛出ValueError"
    except ValueError as e:
        print(f"[ERROR HANDLING] 设置不存在的方案: 正确抛出ValueError: {e}")
    
    print("[ERROR HANDLING] 所有错误处理测试通过")


