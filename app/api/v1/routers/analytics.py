from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.db.models import User

from app.schemas.analytics import (
    SubjectTopicMasteryResponse,
)
from app.services.analytics_service import (
    get_subject_topic_mastery,
)

from app.api.deps import get_current_user, get_db


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get(
    "/subjects/{subject_id}/topic-mastery",
    response_model=SubjectTopicMasteryResponse,
)
def subject_topic_mastery(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    return get_subject_topic_mastery(
        db,
        user_id=current_user.id,
        subject_id=subject_id,
    )