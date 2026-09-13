from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.db.models import StudyPlan, StudyTask
from app.schemas.study_plans import StudyPlanGenerateRequest, StudyPlanOut, StudyTaskOut, TaskStatusUpdate
from app.services.study_plan_service import generate_plan

router = APIRouter(prefix="/study-plans", tags=["study-plans"])


@router.get("", response_model=list[StudyPlanOut])
def list_plans(db: DbSession, user: CurrentUser):
    return list(db.scalars(select(StudyPlan).where(StudyPlan.user_id == user.id).order_by(StudyPlan.created_at.desc())).all())


@router.post("/generate", response_model=StudyPlanOut, status_code=201)
def create_plan(payload: StudyPlanGenerateRequest, db: DbSession, user: CurrentUser):
    return generate_plan(db, user.id, payload)


@router.get("/{plan_id}")
def get_plan(plan_id: int, db: DbSession, user: CurrentUser):
    plan = db.scalar(select(StudyPlan).where(StudyPlan.id == plan_id, StudyPlan.user_id == user.id))
    if plan is None:
        raise HTTPException(404, "Study plan not found")
    tasks = list(db.scalars(select(StudyTask).where(StudyTask.plan_id == plan.id).order_by(StudyTask.task_date, StudyTask.sort_order)).all())
    return {**StudyPlanOut.model_validate(plan).model_dump(), "tasks": [StudyTaskOut.model_validate(t).model_dump() for t in tasks]}


@router.patch("/tasks/{task_id}", response_model=StudyTaskOut)
def update_task(task_id: int, payload: TaskStatusUpdate, db: DbSession, user: CurrentUser):
    task = db.scalar(select(StudyTask).join(StudyPlan, StudyPlan.id == StudyTask.plan_id).where(StudyTask.id == task_id, StudyPlan.user_id == user.id))
    if task is None:
        raise HTTPException(404, "Study task not found")
    task.status = payload.status
    task.completed_at = datetime.now(timezone.utc) if payload.status == "COMPLETED" else None
    db.commit(); db.refresh(task)
    return task
