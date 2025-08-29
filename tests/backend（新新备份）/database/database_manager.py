from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any, Union
from uuid import uuid4
from functools import wraps
import inspect
from backend.utils.logger import logger
from backend.agents.message_models import Patch

from .schemas.research_tree import (
    Snapshot,
    ProblemNode,
    SolutionNode,
    Node,
    NodeType,
    ProblemType,
)

from backend.database.schemas.request_models import (
    ProblemRequest,
    SolutionRequest,
    SetSelectedSolutionRequest,
)


@dataclass
class RelatedSolutions:
    ancestors: List[str]
    descendants: List[str]
    siblings: List[str]


def action_decorator(func):
    """动作装饰器，添加publish_message_callback参数并在执行后自动发布消息"""
    @wraps(func)
    async def wrapper(self, *args, publish_message_callback: Optional[Callable] = None, **kwargs):
        # 获取函数名作为action_type
        action_type = func.__name__
        
        # 获取参数
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()
        params = {k: v for k, v in bound_args.arguments.items() if k != 'self'}
        
        try:
            # 调用原始函数
            if inspect.iscoroutinefunction(func):
                result = await func(self, *args, **kwargs)
            else:
                result = func(self, *args, **kwargs)
                
            # 构建成功结果
            success_result = {
                "success": True,
                "message": f"操作成功: {action_type}",
                "snapshot_id": result.id if hasattr(result, 'id') else "",
                "data": result.model_dump() if hasattr(result, 'model_dump') else result
            }
            
            # 发布消息
            if publish_message_callback:
                await self._publish_user_action_message(
                    publish_message_callback, action_type, params, success_result
                )
                
            return success_result
            
        except Exception as e:
            logger.error(f"执行操作失败: {action_type} - {e}")
            error_result = {
                "success": False,
                "message": f"操作失败: {str(e)}",
                "snapshot_id": "",
                "data": {}
            }
            
            # 发布错误消息
            if publish_message_callback:
                await self._publish_user_action_message(
                    publish_message_callback, action_type, params, error_result, is_error=True
                )
                
            return error_result
            
    return wrapper


def query_decorator(func):
    """查询装饰器，统一处理查询操作"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"查询失败: {func.__name__} - {e}")
            return {
                "success": False,
                "message": f"查询失败: {str(e)}"
            }
    return wrapper


class DatabaseManager:
    def __init__(self) -> None:
        """内存型数据库管理器，维护不可变的快照序列。

        每次修改（增删改）都会在当前快照的深拷贝上进行，随后提交为新的快照，
        从而保证历史快照不受后续修改影响。
        """
        self.snapshot_map: Dict[str, Snapshot] = {}
        self.current_snapshot_id: Optional[str] = None
        self._init_empty_snapshot()

    def _init_empty_snapshot(self) -> None:
        """初始化空快照。"""
        snapshot_id = str(uuid4())
        snapshot = Snapshot(id=snapshot_id, roots=[])
        self.snapshot_map[snapshot_id] = snapshot
        self.current_snapshot_id = snapshot_id

    def get_current_snapshot(self) -> Snapshot:
        """获取当前快照。"""
        assert self.current_snapshot_id is not None
        return self.snapshot_map[self.current_snapshot_id]

    # ---------------- 内部工具：查找/拷贝/提交 ----------------
    def _clone_node(self, node: Node) -> Node:
        """深拷贝任意节点（Problem/Solution），递归复制 children，生成新ID的克隆或保留原ID？

        注意：为保持"快照版本之间可以对比同一节点"的能力，这里保留原ID。
        只有在业务上需要"派生新节点"（如 fork 子树）时才创建新ID。
        """
        if isinstance(node, ProblemNode):
            cloned = ProblemNode(
                id=node.id,
                title=node.title,
                problem_type=node.problem_type,
                significance=node.significance,
                criteria=node.criteria,
                selected_solution_id=node.selected_solution_id,
                children=[],
            )
        else:
            assert isinstance(node, SolutionNode)
            cloned = SolutionNode(
                id=node.id,
                title=node.title,
                top_level_thoughts=node.top_level_thoughts,
                plan_justification=node.plan_justification,
                implementation_plan=node.implementation_plan,
                state=node.state,
                final_report=node.final_report,
                children=[],
            )
        cloned.children = [self._clone_node(c) for c in node.children]
        return cloned

    def _clone_roots(self, roots: List[Node]) -> List[Node]:
        """深拷贝根节点列表（及其整棵子树）。"""
        return [self._clone_node(r) for r in roots]

    def _find_node_in(self, nodes: List[Node], node_id: str) -> Optional[Node]:
        for n in nodes:
            if n.id == node_id:
                return n
            child = self._find_node_in(n.children, node_id)
            if child is not None:
                return child
        return None

    def _find_parent_in(self, nodes: List[Node], node_id: str) -> Optional[Node]:
        for n in nodes:
            for c in n.children:
                if c.id == node_id:
                    return n
            parent = self._find_parent_in(n.children, node_id)
            if parent is not None:
                return parent
        return None

    def _commit(self, roots: List[Node]) -> Snapshot:
        """写入新快照，传入的 roots 必须是深拷贝后的可独立修改树。"""
        new_id = str(uuid4())
        new_snapshot = Snapshot(id=new_id, roots=roots)
        self.snapshot_map[new_id] = new_snapshot
        self.current_snapshot_id = new_id
        return new_snapshot

    # ---------- CRUD for research tree ----------
    @action_decorator
    async def add_root_problem(self, new_problem: ProblemRequest) -> Snapshot:
        """添加根实施问题，并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        root = ProblemNode(
            id=str(uuid4()),
            title=new_problem.title,
            problem_type=ProblemType.IMPLEMENTATION,
            significance=new_problem.significance,
            criteria=new_problem.criteria,
            children=[],
        )
        new_roots.append(root)
        return self._commit(new_roots)

    def _create_problem(self, new_problem: ProblemRequest) -> ProblemNode:
        if new_problem.id is not None:
            node = self._find_node_in(self.get_current_snapshot().roots, new_problem.id)
            if isinstance(node, ProblemNode):
                return self._clone_node(node)
        return ProblemNode(
            id=str(uuid4()), 
            title=new_problem.title, 
            problem_type=new_problem.problem_type, 
            significance=new_problem.significance, 
            criteria=new_problem.criteria, 
            children=[]
        )

    @action_decorator
    async def update_root_problem(self, problem_id: str, new_problem: ProblemRequest) -> Snapshot:
        """更新根问题的元数据（标题/价值/标准/类型），并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        found = False
        for node in new_roots:
            if isinstance(node, ProblemNode) and node.id == problem_id:
                if new_problem.title is not None:
                    node.title = new_problem.title
                if new_problem.significance is not None:
                    node.significance = new_problem.significance
                if new_problem.criteria is not None:
                    node.criteria = new_problem.criteria
                if new_problem.problem_type is not None:
                    # 根问题不允许改为 CONDITIONAL
                    if new_problem.problem_type == ProblemType.CONDITIONAL:
                        raise ValueError("Root problem cannot be CONDITIONAL")
                    node.problem_type = new_problem.problem_type
                found = True
                break
        if not found:
            raise KeyError("Root problem not found")
        return self._commit(new_roots)

    @action_decorator
    async def delete_root_problem(self, problem_id: str) -> Snapshot:
        """删除根问题及其子树，并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        before = len(new_roots)
        new_roots = [n for n in new_roots if n.id != problem_id]
        if len(new_roots) == before:
            raise KeyError("Root problem not found")
        return self._commit(new_roots)

    @action_decorator
    async def create_solution(self, problem_id: str, new_solution: SolutionRequest) -> Snapshot:
        """在指定问题下创建一个解决方案，并提交为新快照。
        智能体创建一个新解决方案或在修改原解决方案时修改了子问题列表，均调用此函数
        后者情况中，需区分沿用原解决方案的子问题和新定义的子问题，前者将包含原解决方案中的问题id，并自动找到该节点复制过来；后者将新建一个子问题。
        如果修改原解决方案时没有修改子问题列表，则调用update_solution函数
        """
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        problem = self._find_node_in(new_roots, problem_id)
        if not isinstance(problem, ProblemNode):
            raise KeyError("Problem node not found")
        if problem.problem_type == ProblemType.CONDITIONAL:
            raise ValueError("Conditional problem cannot have solutions")
        children = []
        if new_solution.children is not None:
            children = [self._create_problem(c) for c in new_solution.children]
        solution = SolutionNode(
            id=str(uuid4()),
            title=new_solution.title,
            top_level_thoughts=new_solution.top_level_thoughts or "",
            plan_justification=new_solution.plan_justification or "",
            implementation_plan=new_solution.implementation_plan or "",
            children=children,
        )
        problem.selected_solution_id = solution.id
        problem.children.append(solution)
        return self._commit(new_roots)

    @action_decorator
    async def delete_solution(self, solution_id: str) -> Snapshot:
        """删除指定解决方案节点，并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        parent = self._find_parent_in(new_roots, solution_id)
        if parent is None:
            raise KeyError("Solution node not found")
        parent.children = [c for c in parent.children if c.id != solution_id]
        return self._commit(new_roots)

    @action_decorator
    async def update_solution(self, solution_id: str, new_solution: SolutionRequest) -> Snapshot:
        """更新解决方案自身内容，并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        node = self._find_node_in(new_roots, solution_id)
        if not isinstance(node, SolutionNode):
            raise KeyError("Solution node not found")
        if new_solution.title is not None:
            node.title = new_solution.title
        if new_solution.top_level_thoughts is not None:
            node.top_level_thoughts = new_solution.top_level_thoughts
        if new_solution.plan_justification is not None:
            node.plan_justification = new_solution.plan_justification
        if new_solution.implementation_plan is not None:
            node.implementation_plan = new_solution.implementation_plan
        if new_solution.state is not None:
            node.state = new_solution.state
        if new_solution.final_report is not None:
            node.final_report = new_solution.final_report
        return self._commit(new_roots)

    @action_decorator
    async def set_selected_solution(self, problem_id: str, solution_id: Optional[str]) -> Snapshot:
        """设置或清空问题的选中方案，并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        node = self._find_node_in(new_roots, problem_id)
        if not isinstance(node, ProblemNode):
            raise KeyError("Problem node not found")
        # 校验 solution_id 属于该问题
        if solution_id is not None:
            if not any(c.id == solution_id for c in node.children if isinstance(c, SolutionNode)):
                raise ValueError("Selected solution is not a child of the problem")
        node.selected_solution_id = solution_id
        return self._commit(new_roots)

    # 添加缺失的action方法
    @action_decorator
    async def update_problem(self, problem_id: str, new_problem: ProblemRequest) -> Snapshot:
        """更新问题节点（非根问题），并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        node = self._find_node_in(new_roots, problem_id)
        if not isinstance(node, ProblemNode):
            raise KeyError("Problem node not found")
        if new_problem.title is not None:
            node.title = new_problem.title
        if new_problem.significance is not None:
            node.significance = new_problem.significance
        if new_problem.criteria is not None:
            node.criteria = new_problem.criteria
        if new_problem.problem_type is not None:
            node.problem_type = new_problem.problem_type
        return self._commit(new_roots)

    @query_decorator
    def get_current_snapshot_query(self) -> Dict:
        """获取当前快照查询"""
        snapshot = self.get_current_snapshot()
        return snapshot.model_dump()

    @query_decorator
    def get_compact_text_tree_query(self) -> Dict:
        """返回仅包含标题与状态的树状文本查询"""
        current = self.get_current_snapshot()

        def render(node: Node, depth: int, parent_problem: Optional[ProblemNode] = None) -> List[str]:
            indent = "  " * depth
            if isinstance(node, ProblemNode):
                line = f"{indent}- [P] {node.title} ({node.problem_type.value})"
                lines = [line]
                for c in node.children:
                    lines.extend(render(c, depth + 1, node))
                return lines
            else:
                assert isinstance(node, SolutionNode)
                # 查找父问题节点的选中方案id
                status_flag = ""
                if parent_problem is not None:
                    if parent_problem.selected_solution_id == node.id:
                        status_flag = "(正启用)"
                    else:
                        status_flag = "(已弃用)"
                line = f"{indent}- [S] {node.title} {status_flag} [{node.state.value}]"
                lines = [line]
                for c in node.children:
                    lines.extend(render(c, depth + 1, None))
                return lines

        lines: List[str] = []
        for r in current.roots:
            lines.extend(render(r, 0, None))
        return {"tree_text": "\n".join(lines)}

    @query_decorator
    def get_node_id_by_title_query(self, title: str, node_type: Optional[NodeType] = None) -> Dict:
        """
        根据标题查找节点查询
        
        Args:
            title: 节点标题
            node_type: 可选的节点类型过滤
            
        Returns:
            找到的节点，如果不存在返回None
        """
        def search_in_nodes(nodes: List[Node]) -> Optional[Node]:
            for node in nodes:
                if node.title == title:
                    if node_type is None or node.type == node_type:
                        return node
                # 递归搜索子节点
                result = search_in_nodes(node.children)
                if result:
                    return result
            return None
        
        node = search_in_nodes(self.get_current_snapshot().roots)
        return {"id": node.id if node else None}

    @query_decorator
    def get_node_by_id_query(self, node_id: str) -> Dict:
        """获取节点查询"""
        node = self._find_node_in(self.get_current_snapshot().roots, node_id)
        result = node.model_dump()
        result.pop("children")
        return {"node": result}

    @query_decorator
    def get_problem_detail_query(self, problem_id: str) -> Dict:
        """获取问题详情查询"""
        node = self._find_node_in(self.get_current_snapshot().roots, problem_id)
        if not isinstance(node, ProblemNode):
            raise KeyError("Problem node not found")
        return {"detail": f"<name>{node.title}</name>\n<significance>\n{node.significance}\n</significance>\n<criteria>\n{node.criteria}\n</criteria>"}

    @query_decorator
    def get_node_children_ids_query(self, node_id: str, only_implementation: bool = False) -> Dict:
        """获取子节点id列表查询，无论节点类型"""
        node = self._find_node_in(self.get_current_snapshot().roots, node_id)
        if not isinstance(node, Node):
            raise KeyError("Node not found")
        if only_implementation:
            return {"children_ids": [c.id for c in node.children if isinstance(c, ProblemNode) and c.problem_type == ProblemType.IMPLEMENTATION]}
        else:
            return {"children_ids": [c.id for c in node.children]}

    @query_decorator
    def get_solution_children_request_map_by_title_query(self, solution_id: str) -> Dict:
        """获取解决方案子问题列表查询"""
        node = self._find_node_in(self.get_current_snapshot().roots, solution_id)
        if not isinstance(node, SolutionNode):
            raise KeyError("Solution node not found")
        problem_request_map = {}
        for c in node.children:
            if isinstance(c, ProblemNode):
                problem_request_map[c.title] = ProblemRequest(
                    id=c.id,
                    title=c.title,
                    significance=c.significance, 
                    criteria=c.criteria,
                    problem_type=c.problem_type
                )
        return {"children_request_map": problem_request_map}

    @query_decorator
    def get_selected_solution_id_query(self, problem_id: str) -> Dict:
        """获取选中解决方案ID查询"""
        node = self._find_node_in(self.get_current_snapshot().roots, problem_id)
        if not isinstance(node, ProblemNode) or node.problem_type != ProblemType.IMPLEMENTATION:
            raise KeyError("Problem node not found or not an implementation problem")    
        return {"selected_solution_id": node.selected_solution_id}

    @query_decorator
    def get_root_problem_id_query(self, node_id: str) -> Dict:
        """获取当前节点所在的树的根节点id查询"""
        roots = self.get_current_snapshot().roots
        for root in roots:
            if self._find_node_in([root], node_id):
                return {"root_problem_id": root.id}
        raise KeyError(f"未找到节点 {node_id} 所在的根问题")

    @query_decorator
    def get_parent_node_id_query(self, node_id: str) -> Dict:
        """获取指定节点的父节点ID查询"""
        node = self._find_parent_in(self.get_current_snapshot().roots, node_id)
        return {"parent_node_id": node.id}

    @query_decorator
    def get_solution_detail_query(self, solution_id: str) -> Dict:
        """获取解决方案详情查询"""
        node = self._find_node_in(self.get_current_snapshot().roots, solution_id)
        if not isinstance(node, SolutionNode):
            raise KeyError("Solution node not found")
        # 组织为XML文档文本
        sub_problems = []
        for c in node.children:
            if isinstance(c, ProblemNode):
                sub_problem_lines = [
                    f"<step type={c.problem_type.value}>",
                    f"<name>{c.title}</name>",
                    f"<significance>",
                    c.significance,
                    f"</significance>",
                    f"<criteria>",
                    c.criteria,
                    f"</criteria>",
                    f"</step>",
                ]
                sub_problems.append("\n".join(sub_problem_lines))
        sub_problems_text = "\n".join(sub_problems)

        result_lines = [
            f"<solution>",
            f"<name>{node.title}</name>",
            f"<top_level_thoughts>",
            node.top_level_thoughts,
            f"</top_level_thoughts>",
            f"<research_plan>",
            sub_problems_text,
            f"</research_plan>",
            f"<implementation_plan>",
            node.implementation_plan,
            f"</implementation_plan>",
            f"<plan_justification>",
            node.plan_justification,
            f"</plan_justification>",
            f"<implementation_plan>",
            node.implementation_plan,
            f"</implementation_plan>",
            f"<final_report>",
            f"{node.final_report if node.final_report else '暂无'}",
            f"</final_report>",
            f"</solution>",
        ]
        return {"detail": "\n".join(result_lines)}

    @query_decorator
    def get_related_solutions_query(self, problem_id: str) -> Dict:
        """获取相关解决方案查询"""
        current = self.get_current_snapshot()
        target = self._find_node_in(current.roots, problem_id)
        if not isinstance(target, ProblemNode):
            raise KeyError("Problem node not found")
        # ancestors: 祖先解决方案
        ancestors: List[str] = []
        # find parent problem then walk upwards
        def find_ancestors(node_id: str) -> None:
            parent = self._find_parent_in(current.roots, node_id)
            if parent is None:
                return
            if isinstance(parent, SolutionNode):
                ancestors.append(parent.id)
                gp = self._find_parent_in(current.roots, parent.id)
                if gp:
                    find_ancestors(gp.id)

        find_ancestors(problem_id)

        # descendants: 所有后代解决方案
        solution_id = target.selected_solution_id
        descendants: List[str] = []

        def walk_desc(n: Node) -> None:
            for c in n.children:
                if isinstance(c, SolutionNode):
                    descendants.append(c.id)
                walk_desc(c)
                
        if solution_id:
            solution_node = self._find_node_in(target.children, solution_id)
            if solution_node:
                walk_desc(solution_node)

        # siblings: 同一父问题下其它解决方案
        siblings: List[str] = [child.id for child in target.children 
                              if isinstance(child, SolutionNode) and child.id != solution_id]

        return {
            "ancestors": ancestors,
            "descendants": descendants,
            "siblings": siblings
        }

    async def _publish_user_action_message(self, publish_message_callback: Callable, action_type: str, params: Dict[str, Any], result: Dict[str, Any], is_error: bool = False) -> None:
        """
        发布用户操作消息
        
        Args:
            publish_message_callback: 发布消息的回调函数
            action_type: 操作类型
            params: 操作参数
            result: 操作结果
            is_error: 是否为错误结果
        """
        try:
            # 构建消息内容
            if is_error:
                title = f"操作失败: {action_type}"
                content = f"操作类型: {action_type}\n参数: {params}\n错误: {result['message']}"
            else:
                title = f"操作成功: {action_type}"
                content = f"操作类型: {action_type}\n参数: {params}\n结果: {result['message']}"
            
            # 创建Patch对象而不是字典
            patch = Patch(
                message_id=None,  # 创建新消息
                role="user",  # 用户操作消息
                title=title,
                content_delta=content,
                action_title=action_type,  # 使用action_title字段
                action_params=params,
                snapshot_id=result.get("snapshot_id", ""),
                visible_node_ids=[],  # 用户操作消息全局可见
                finished=True
            )
            
            # 调用回调函数发布消息
            await publish_message_callback(patch)
            
        except Exception as e:
            # 发布消息失败时记录日志，但不影响主操作
            logger.error(f"发布用户操作消息失败: {e}")