from fastapi import APIRouter, HTTPException

from backend.project_manager import shared_database_manager, shared_message_manager
from backend.utils.logger import logger

router = APIRouter(prefix="/research-tree", tags=["research-tree"])

# 使用共享的数据库管理器实例
db = shared_database_manager
sm = shared_message_manager

from backend.database.schemas.request_models import (
    ProblemRequest,
    SolutionRequest,
    SetSelectedSolutionRequest,
)

@router.get("/snapshots/current-id")
def get_current_snapshot_id():
    return db.get_current_snapshot_id_query()

@router.get("/snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: str):
    return db.get_snapshot_query(snapshot_id)

@router.post("/problems/root")
async def create_root_problem(body: ProblemRequest):
    try:
        return await db.add_root_problem(body, publish_message_callback=sm.publish_patch)
    except Exception as e:
        logger.error(f"请求创建根问题失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/problems/root/{problem_id}")
async def update_root_problem(problem_id: str, body: ProblemRequest):
    try:
        return await db.update_root_problem(problem_id, body, publish_message_callback=sm.publish_patch)
    except KeyError as e:
        logger.error(f"请求更新根问题失败: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"请求更新根问题失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/problems/root/{problem_id}")
async def delete_root_problem(problem_id: str):
    try:
        return await db.delete_root_problem(problem_id, publish_message_callback=sm.publish_patch)
    except KeyError as e:
        logger.error(f"请求删除根问题失败: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/problems/{problem_id}/solutions")
async def create_solution(problem_id: str, body: SolutionRequest):
    try:
        return await db.create_solution(problem_id, body, publish_message_callback=sm.publish_patch)
    except KeyError as e:
        logger.error(f"请求创建解决方案失败: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/solutions/{solution_id}")
async def delete_solution(solution_id: str):
    try:
        return await db.delete_solution(solution_id, publish_message_callback=sm.publish_patch)
    except KeyError as e:
        logger.error(f"请求删除解决方案失败: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/solutions/{solution_id}")
async def update_solution(solution_id: str, body: SolutionRequest):
    try:
        return await db.update_solution(solution_id, body, publish_message_callback=sm.publish_patch)
    except KeyError as e:
        logger.error(f"请求更新解决方案失败: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/problems/{problem_id}/selected-solution")
async def set_selected_solution(problem_id: str, body: SetSelectedSolutionRequest):
    try:
        return await db.set_selected_solution(problem_id, body.solution_id, publish_message_callback=sm.publish_patch)
    except KeyError as e:
        logger.error(f"请求设置选中解决方案失败: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"请求设置选中解决方案失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
