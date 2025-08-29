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
    finishing_task: str = ""
    plan_justification: str = ""
    state: SolutionState = SolutionState.IN_PROGRESS
    final_report: Optional[str] = None


Node.update_forward_refs()


class Snapshot(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    roots: List[Node] = Field(default_factory=list)


# 请求模型
class CreateRootProblemRequest(BaseModel):
    title: str
    significance: str
    criteria: str
    problem_type: Literal[ProblemType.IMPLEMENTATION] = ProblemType.IMPLEMENTATION


class UpdateProblemRequest(BaseModel):
    title: Optional[str] = None
    significance: Optional[str] = None
    criteria: Optional[str] = None
    problem_type: Optional[ProblemType] = None

class CreateProblemRequest(BaseModel):
    id: Optional[str] = None # 如果id为空，则代表新创建；否则找到id对应的节点，并直接使用该问题节点，弃用请求中的该问题信息
    title: str
    significance: str
    criteria: str
    problem_type: Literal[ProblemType.IMPLEMENTATION] = ProblemType.IMPLEMENTATION

class CreateSolutionRequest(BaseModel):
    title: str
    top_level_thoughts: Optional[str] = None
    plan_justification: Optional[str] = None
    finishing_task: Optional[str] = None
    children: Optional[List[CreateProblemRequest]] = None

class UpdateSolutionRequest(BaseModel):
    title: Optional[str] = None
    top_level_thoughts: Optional[str] = None
    plan_justification: Optional[str] = None
    finishing_task: Optional[str] = None
    state: Optional[SolutionState] = None
    final_report: Optional[str] = None


class SetSelectedSolutionRequest(BaseModel):
    solution_id: Optional[str] = None


# 响应模型
class SnapshotResponse(BaseModel):
    snapshot: Snapshot


