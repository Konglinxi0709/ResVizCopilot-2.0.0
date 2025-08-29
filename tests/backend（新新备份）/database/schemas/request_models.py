from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Literal
from backend.database.schemas.research_tree import ProblemType, SolutionState, Snapshot


# 请求模型
class ProblemRequest(BaseModel):
    id: Optional[str] = None
    title: str
    significance: str
    criteria: str
    problem_type: ProblemType = ProblemType.IMPLEMENTATION

class SolutionRequest(BaseModel):
    title: str
    top_level_thoughts: Optional[str] = None
    implementation_plan: Optional[str] = None
    plan_justification: Optional[str] = None
    state: Optional[SolutionState] = SolutionState.IN_PROGRESS
    final_report: Optional[str] = None
    children: Optional[List[ProblemRequest]] = None


class SetSelectedSolutionRequest(BaseModel):
    solution_id: Optional[str] = None
