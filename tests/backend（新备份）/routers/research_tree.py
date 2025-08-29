from fastapi import APIRouter, HTTPException

from backend.database.DatabaseManager import DatabaseManager, RelatedSolutions
from backend.database.schemas.research_tree import (
    CreateRootProblemRequest,
    UpdateProblemRequest,
    CreateSolutionRequest,
    UpdateSolutionRequest,
    SetSelectedSolutionRequest,
    SnapshotResponse,
)


router = APIRouter(prefix="/research-tree", tags=["research-tree"])
db = DatabaseManager()


@router.get("/snapshots/current", response_model=SnapshotResponse)
def get_current_snapshot():
    return SnapshotResponse(snapshot=db.get_current_snapshot())


@router.post("/problems/root", response_model=SnapshotResponse)
def create_root_problem(body: CreateRootProblemRequest):
    try:
        snap = db.add_root_problem(body)
        return SnapshotResponse(snapshot=snap)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/problems/root/{problem_id}", response_model=SnapshotResponse)
def update_root_problem(problem_id: str, body: UpdateProblemRequest):
    try:
        snap = db.update_root_problem(problem_id, body)
        return SnapshotResponse(snapshot=snap)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/problems/root/{problem_id}", response_model=SnapshotResponse)
def delete_root_problem(problem_id: str):
    try:
        snap = db.delete_root_problem(problem_id)
        return SnapshotResponse(snapshot=snap)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/problems/{problem_id}/solutions", response_model=SnapshotResponse)
def create_solution(problem_id: str, body: CreateSolutionRequest):
    try:
        snap = db.create_solution(problem_id, body)
        return SnapshotResponse(snapshot=snap)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/solutions/{solution_id}", response_model=SnapshotResponse)
def delete_solution(solution_id: str):
    try:
        snap = db.delete_solution(solution_id)
        return SnapshotResponse(snapshot=snap)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/solutions/{solution_id}", response_model=SnapshotResponse)
def update_solution(solution_id: str, body: UpdateSolutionRequest):
    try:
        snap = db.update_solution(solution_id, body)
        return SnapshotResponse(snapshot=snap)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/problems/{problem_id}/selected-solution", response_model=SnapshotResponse)
def set_selected_solution(problem_id: str, body: SetSelectedSolutionRequest):
    try:
        snap = db.set_selected_solution(problem_id, body.solution_id)
        return SnapshotResponse(snapshot=snap)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
