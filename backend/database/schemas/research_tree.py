from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal

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