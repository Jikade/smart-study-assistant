from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
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

@router.get("/{export_id}/download")
def download_export(export_id: int, db: DbSession, user: CurrentUser):
    job = db.get(ExportJob, export_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Export not found")
    if job.status != "COMPLETED" or not job.file_url:
        raise HTTPException(409, "Export is not ready")

    path = Path(job.file_url)
    if not path.is_file():
        raise HTTPException(404, "Export file not found")

    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if job.file_format == "DOCX"
        else "application/pdf"
    )
    return FileResponse(path=str(path), filename=path.name, media_type=media_type)
