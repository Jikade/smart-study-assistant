from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.db.models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(db: DbSession, user: CurrentUser, unread_only: bool = False):
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    rows = db.scalars(stmt.order_by(Notification.created_at.desc()).limit(100)).all()
    return [{"id": n.id, "type": n.notification_type, "title": n.title, "message": n.message, "payload": n.payload, "is_read": n.is_read, "read_at": n.read_at, "created_at": n.created_at} for n in rows]


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, db: DbSession, user: CurrentUser):
    row = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if row is None: raise HTTPException(404, "Notification not found")
    row.is_read = True; row.read_at = datetime.now(timezone.utc)
    db.commit(); return {"ok": True}
