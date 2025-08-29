from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from uuid import uuid4

from .schemas.research_tree import (
    Snapshot,
    ProblemNode,
    SolutionNode,
    Node,
    NodeType,
    ProblemType,
    CreateRootProblemRequest,
    UpdateProblemRequest,
    CreateProblemRequest,
    CreateSolutionRequest,
    UpdateSolutionRequest,
)


@dataclass
class RelatedSolutions:
    ancestors: List[str]
    descendants: List[str]
    siblings: List[str]


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

        注意：为保持“快照版本之间可以对比同一节点”的能力，这里保留原ID。
        只有在业务上需要“派生新节点”（如 fork 子树）时才创建新ID。
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
                finishing_task=node.finishing_task,
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
    def add_root_problem(self, input: CreateRootProblemRequest) -> Snapshot:
        """添加根实施问题，并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        root = ProblemNode(
            id=str(uuid4()),
            title=input.title,
            problem_type=input.problem_type,
            significance=input.significance,
            criteria=input.criteria,
            children=[],
        )
        new_roots.append(root)
        return self._commit(new_roots)

    def _create_problem(self, input: CreateProblemRequest) -> ProblemNode:
        if input.id is not None:
            node = self._find_node_in(self.get_current_snapshot().roots, input.id)
            if isinstance(node, ProblemNode):
                return self._clone_node(node)
        return ProblemNode(
            id=str(uuid4()), 
            title=input.title, 
            problem_type=input.problem_type, 
            significance=input.significance, 
            criteria=input.criteria, 
            children=[]
        )

    def update_root_problem(self, problem_id: str, input: UpdateProblemRequest) -> Snapshot:
        """更新根问题的元数据（标题/价值/标准/类型），并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        found = False
        for node in new_roots:
            if isinstance(node, ProblemNode) and node.id == problem_id:
                if input.title is not None:
                    node.title = input.title
                if input.significance is not None:
                    node.significance = input.significance
                if input.criteria is not None:
                    node.criteria = input.criteria
                if input.problem_type is not None:
                    # 根问题不允许改为 CONDITIONAL
                    if input.problem_type == ProblemType.CONDITIONAL:
                        raise ValueError("Root problem cannot be CONDITIONAL")
                    node.problem_type = input.problem_type
                found = True
                break
        if not found:
            raise KeyError("Root problem not found")
        return self._commit(new_roots)

    def delete_root_problem(self, problem_id: str) -> Snapshot:
        """删除根问题及其子树，并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        before = len(new_roots)
        new_roots = [n for n in new_roots if n.id != problem_id]
        if len(new_roots) == before:
            raise KeyError("Root problem not found")
        return self._commit(new_roots)


    def create_solution(self, problem_id: str, input: CreateSolutionRequest) -> Snapshot:
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
        if input.children is not None:
            children = [self._create_problem(c) for c in input.children]
        solution = SolutionNode(
            id=str(uuid4()),
            title=input.title,
            top_level_thoughts=input.top_level_thoughts or "",
            plan_justification=input.plan_justification or "",
            finishing_task=input.finishing_task or "",
            children=children,
        )
        problem.children.append(solution)
        return self._commit(new_roots)

    def delete_solution(self, solution_id: str) -> Snapshot:
        """删除指定解决方案节点，并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        parent = self._find_parent_in(new_roots, solution_id)
        if parent is None:
            raise KeyError("Solution node not found")
        parent.children = [c for c in parent.children if c.id != solution_id]
        return self._commit(new_roots)

    def update_solution(self, solution_id: str, input: UpdateSolutionRequest) -> Snapshot:
        """更新解决方案自身内容，并提交为新快照。"""
        current = self.get_current_snapshot()
        new_roots = self._clone_roots(current.roots)
        node = self._find_node_in(new_roots, solution_id)
        if not isinstance(node, SolutionNode):
            raise KeyError("Solution node not found")
        if input.title is not None:
            node.title = input.title
        if input.top_level_thoughts is not None:
            node.top_level_thoughts = input.top_level_thoughts
        if input.plan_justification is not None:
            node.plan_justification = input.plan_justification
        if input.finishing_task is not None:
            node.finishing_task = input.finishing_task
        if input.state is not None:
            node.state = input.state
        if input.final_report is not None:
            node.final_report = input.final_report
        return self._commit(new_roots)

    def set_selected_solution(self, problem_id: str, solution_id: Optional[str]) -> Snapshot:
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



    def get_compact_text_tree(self) -> str:
        """返回仅包含标题与状态的树状文本"""
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
        return "\n".join(lines)

    def get_related_solutions(self, solution_id: str) -> RelatedSolutions:
        current = self.get_current_snapshot()
        target = self._find_node_in(current.roots, solution_id)
        if not isinstance(target, SolutionNode):
            raise KeyError("Solution node not found")
        # ancestors: 祖先解决方案
        ancestors: List[str] = []
        # find parent problem then walk upwards
        def find_ancestors(node_id: str) -> None:
            parent = self._find_parent_in(current.roots, node_id)
            if parent is None:
                return
            if isinstance(parent, ProblemNode):
                gp = self._find_parent_in(current.roots, parent.id)
                if isinstance(gp, SolutionNode):
                    ancestors.append(gp.id)
                    find_ancestors(gp.id)

        find_ancestors(solution_id)

        # descendants: 所有后代解决方案
        descendants: List[str] = []

        def walk_desc(n: Node) -> None:
            for c in n.children:
                if isinstance(c, SolutionNode):
                    descendants.append(c.id)
                walk_desc(c)

        walk_desc(target)

        # siblings: 同一父问题下其它解决方案
        siblings: List[str] = []
        parent = self._find_parent_in(current.roots, solution_id)
        if isinstance(parent, ProblemNode):
            siblings = [c.id for c in parent.children if isinstance(c, SolutionNode) and c.id != solution_id]

        return RelatedSolutions(ancestors=ancestors, descendants=descendants, siblings=siblings)

    def get_solution_detail(self, solution_id: str) -> str:
        node = self._find_node_in(self.get_current_snapshot().roots, solution_id)
        if not isinstance(node, SolutionNode):
            raise KeyError("Solution node not found")
        # 组织为XML文档文本
        implementation_steps = []
        for c in node.children:
            if isinstance(c, ProblemNode):
                step_lines = [
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
                implementation_steps.append("\n".join(step_lines))
        implementation_steps_text = "\n".join(implementation_steps)

        result_lines = [
            f"<name>{node.title}</name>",
            f"<top_level_thoughts>",
            node.top_level_thoughts,
            f"</top_level_thoughts>",
            f"<implementation_plan>",
            implementation_steps_text,
            f"</implementation_plan>",
            f"<plan_justification>",
            node.plan_justification,
            f"</plan_justification>",
            f"<finishing_task>",
            node.finishing_task,
            f"</finishing_task>",
            f"<final_report>",
            f"{node.final_report if node.final_report else '暂无'}",
            f"</final_report>"
        ]
        return "\n".join(result_lines)

    def get_problem_detail(self, problem_id: str) -> str:
        node = self._find_node_in(self.get_current_snapshot().roots, problem_id)
        if not isinstance(node, ProblemNode):
            raise KeyError("Problem node not found")
        return f"<name>{node.title}</name>\n<significance>{node.significance}</significance>\n<criteria>{node.criteria}</criteria>"

