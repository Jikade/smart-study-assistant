from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.db.models import ExportJob
from app.services.export_service import create_export

router = APIRouter(prefix="/exports", tags=["exports"])


class ExportRequest(BaseModel):
    resource_type: str = Field(pattern="^(QUIZ|FLASHCARD_DECK|STUDY_PLAN)$")
    resource_id: int
    file_format: str = Field(pattern="^(PDF|DOCX)$")


@router.post("", status_code=201)
def export(payload: ExportRequest, db: DbSession, user: CurrentUser):
    try:
        job = create_export(db, user.id, payload.resource_type, payload.resource_id, payload.file_format)
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"id": job.id, "status": job.status, "file_url": job.file_url, "file_format": job.file_format}


@router.get("")
def list_exports(db: DbSession, user: CurrentUser):
    rows = db.scalars(select(ExportJob).where(ExportJob.user_id == user.id).order_by(ExportJob.created_at.desc()).limit(100)).all()
    return [{"id": r.id, "resource_type": r.resource_type, "resource_id": r.resource_id, "file_format": r.file_format, "status": r.status, "file_url": r.file_url, "error_message": r.error_message, "created_at": r.created_at} for r in rows]
