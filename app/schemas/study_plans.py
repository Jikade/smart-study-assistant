from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class StudyPlanGenerateRequest(BaseModel):
    subject_id: int | None = None
    title: str = Field(min_length=1, max_length=300)
    start_date: date
    exam_date: date
    daily_minutes: int = Field(default=60, gt=0, le=720)


class StudyPlanOut(ORMModel):
    id: int
    user_id: int
    subject_id: int | None = None
    title: str
    start_date: date
    exam_date: date | None = None
    daily_minutes: int
    status: str
    generated_by_ai: bool
    generation_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class StudyTaskOut(ORMModel):
    id: int
    plan_id: int
    task_date: date
    task_type: str
    title: str
    description: str | None = None
    estimated_minutes: int
    sort_order: int
    status: str
    completed_at: datetime | None = None


class TaskStatusUpdate(BaseModel):
    status: str = Field(pattern="^(PENDING|IN_PROGRESS|COMPLETED|SKIPPED)$")
