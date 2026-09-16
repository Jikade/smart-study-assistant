from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_db,
)
from app.db.models import User
from app.schemas.analytics import (
    PracticeRecommendationResponse,
    SubjectTopicMasteryResponse,
    WeakTopicsResponse,
)
from app.services.analytics_service import (
    get_practice_recommendations,
    get_subject_topic_mastery,
    get_weak_topics,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


# =========================================================
# TOPIC MASTERY
# =========================================================


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

@router.get(
    "/subjects/{subject_id}/practice-recommendations",
    response_model=(
        PracticeRecommendationResponse
    ),
)
def practice_recommendations(
    subject_id: int,
    db: DbSession,
    user: CurrentUser,
):
    return get_practice_recommendations(
        db,
        user_id=user.id,
        subject_id=subject_id,
    )

# =========================================================
# WEAK TOPICS
# =========================================================


@router.get(
    "/subjects/{subject_id}/weak-topics",
    response_model=WeakTopicsResponse,
)
def subject_weak_topics(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    return get_weak_topics(
        db,
        user_id=current_user.id,
        subject_id=subject_id,
    )