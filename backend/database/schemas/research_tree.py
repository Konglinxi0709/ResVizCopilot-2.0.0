from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal, Dict, Any

from pydantic import BaseModel, Field


class SolutionState(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    IN_PROGRESS = "in_progress"


class NodeType(str, Enum):
    PROBLEM = "problem"
    SOLUTION = "solution"


class ProblemType(str, Enum):
    IMPLEMENTATION = "implementation"
    CONDITIONAL = "conditional"  # 条件问题没有子solution节点


class Node(BaseModel):
    id: str
    type: NodeType
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    children: List[Node] = Field(default_factory=list)


class ProblemNode(Node):
    type: Literal[NodeType.PROBLEM] = NodeType.PROBLEM
    problem_type: ProblemType
    selected_solution_id: Optional[str] = None
    significance: str
    criteria: str


class SolutionNode(Node):
    type: Literal[NodeType.SOLUTION] = NodeType.SOLUTION
    top_level_thoughts: str = ""
    implementation_plan: str = ""
    plan_justification: str = ""
    state: SolutionState = SolutionState.IN_PROGRESS
    final_report: Optional[str] = None


Node.update_forward_refs()


class Snapshot(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    roots: List[Node] = Field(default_factory=list)

    def model_dump(self, **kwargs):
        # 递归序列化所有节点
        def serialize_node(node):
            if isinstance(node, ProblemNode):
                return {
                    "id": node.id,
                    "type": node.type,
                    "title": node.title,
                    "created_at": node.created_at,
                    "problem_type": node.problem_type,
                    "selected_solution_id": node.selected_solution_id,
                    "significance": node.significance,
                    "criteria": node.criteria,
                    "children": [serialize_node(child) for child in node.children]
                }
            elif isinstance(node, SolutionNode):
                return {
                    "id": node.id,
                    "type": node.type,
                    "title": node.title,
                    "created_at": node.created_at,
                    "top_level_thoughts": node.top_level_thoughts,
                    "implementation_plan": node.implementation_plan,
                    "plan_justification": node.plan_justification,
                    "state": node.state,
                    "final_report": node.final_report,
                    "children": [serialize_node(child) for child in node.children]
                }
            else:
                return {
                    "id": node.id,
                    "type": node.type,
                    "title": node.title,
                    "created_at": node.created_at,
                    "children": [serialize_node(child) for child in node.children]
                }

        return {
            "id": self.id,
            "created_at": self.created_at,
            "roots": [serialize_node(root) for root in self.roots]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Snapshot':
        """
        从字典数据重建快照，正确处理节点类型识别
        
        Args:
            data: 包含快照数据的字典
            
        Returns:
            重建的快照对象
        """
        def deserialize_node(node_data: Dict[str, Any]) -> Node:
            """递归反序列化节点，根据type字段和特有字段判断具体类型"""
            node_type = node_data.get("type")
            
            if node_type == NodeType.PROBLEM:
                # 重建ProblemNode
                return ProblemNode(
                    id=node_data["id"],
                    type=NodeType.PROBLEM,
                    title=node_data["title"],
                    created_at=datetime.fromisoformat(node_data["created_at"]) if isinstance(node_data["created_at"], str) else node_data["created_at"],
                    problem_type=ProblemType(node_data["problem_type"]) if node_data.get("problem_type") else ProblemType.IMPLEMENTATION,
                    selected_solution_id=node_data.get("selected_solution_id"),
                    significance=node_data.get("significance", ""),
                    criteria=node_data.get("criteria", ""),
                    children=[deserialize_node(child) for child in node_data.get("children", [])]
                )
            elif node_type == NodeType.SOLUTION:
                # 重建SolutionNode
                return SolutionNode(
                    id=node_data["id"],
                    type=NodeType.SOLUTION,
                    title=node_data["title"],
                    created_at=datetime.fromisoformat(node_data["created_at"]) if isinstance(node_data["created_at"], str) else node_data["created_at"],
                    top_level_thoughts=node_data.get("top_level_thoughts", ""),
                    implementation_plan=node_data.get("implementation_plan", ""),
                    plan_justification=node_data.get("plan_justification", ""),
                    state=SolutionState(node_data["state"]) if node_data.get("state") else SolutionState.IN_PROGRESS,
                    final_report=node_data.get("final_report"),
                    children=[deserialize_node(child) for child in node_data.get("children", [])]
                )
            else:
                # 未知类型，尝试推断
                if "problem_type" in node_data:
                    # 有problem_type字段，应该是ProblemNode
                    return ProblemNode(
                        id=node_data["id"],
                        type=NodeType.PROBLEM,
                        title=node_data["title"],
                        created_at=datetime.fromisoformat(node_data["created_at"]) if isinstance(node_data["created_at"], str) else node_data["created_at"],
                        problem_type=ProblemType(node_data["problem_type"]) if node_data.get("problem_type") else ProblemType.IMPLEMENTATION,
                        selected_solution_id=node_data.get("selected_solution_id"),
                        significance=node_data.get("significance", ""),
                        criteria=node_data.get("criteria", ""),
                        children=[deserialize_node(child) for child in node_data.get("children", [])]
                    )
                elif "top_level_thoughts" in node_data or "implementation_plan" in node_data or "plan_justification" in node_data:
                    # 有解决方案特有字段，应该是SolutionNode
                    return SolutionNode(
                        id=node_data["id"],
                        type=NodeType.SOLUTION,
                        title=node_data["title"],
                        created_at=datetime.fromisoformat(node_data["created_at"]) if isinstance(node_data["created_at"], str) else node_data["created_at"],
                        top_level_thoughts=node_data.get("top_level_thoughts", ""),
                        implementation_plan=node_data.get("implementation_plan", ""),
                        plan_justification=node_data.get("plan_justification", ""),
                        state=SolutionState(node_data["state"]) if node_data.get("state") else SolutionState.IN_PROGRESS,
                        final_report=node_data.get("final_report"),
                        children=[deserialize_node(child) for child in node_data.get("children", [])]
                    )
                else:
                    # 无法确定类型，使用基础Node
                    return Node(
                        id=node_data["id"],
                        type=NodeType(node_data.get("type", NodeType.PROBLEM)),
                        title=node_data["title"],
                        created_at=datetime.fromisoformat(node_data["created_at"]) if isinstance(node_data["created_at"], str) else node_data["created_at"],
                        children=[deserialize_node(child) for child in node_data.get("children", [])]
                    )
        
        # 重建快照
        return cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            roots=[deserialize_node(root) for root in data.get("roots", [])]
        )