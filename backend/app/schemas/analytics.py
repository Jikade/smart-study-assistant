from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


MasteryStatus = Literal[
    "NOT_ENOUGH_DATA",
    "WEAK",
    "DEVELOPING",
    "STRONG",
]


class TopicMasteryItem(BaseModel):
    section_id: int
    title: str

    attempts: int
    correct_answers: int
    wrong_answers: int

    mastery_score: float
    status: MasteryStatus

    last_practiced_at: datetime | None = None


class TopicMasterySummary(BaseModel):
    total_topics: int

    weak_topics: int
    developing_topics: int
    strong_topics: int

    not_enough_data_topics: int


class SubjectTopicMasteryResponse(BaseModel):
    subject_id: int
    subject_name: str

    summary: TopicMasterySummary

    topics: list[TopicMasteryItem]


class WeakTopicsResponse(BaseModel):
    subject_id: int
    subject_name: str

    threshold: float
    minimum_attempts: int

    count: int

    topics: list[TopicMasteryItem]

class PracticeRecommendationItem(
    TopicMasteryItem
):
    rank: int
    reason: str


class PracticeRecommendationResponse(
    BaseModel
):
    subject_id: int
    subject_name: str

    strategy: str

    recommendation_count: int
    skipped_strong_topics: int

    recommendations: list[
        PracticeRecommendationItem
    ]

# =========================================================
# SPACED PRACTICE / STUDY PLAN
# =========================================================


class SpacedPracticeItem(BaseModel):
    section_id: int
    title: str

    attempts: int
    correct_answers: int
    wrong_answers: int
    mastery_score: float
    mastery_status: str

    interval_days: int

    last_practiced_at: (
        datetime
        | None
    )

    next_review_at: datetime

    scheduled_date: date

    due_status: str

    priority_score: float

    reason: str


class StudyPlanDay(BaseModel):
    date: date

    item_count: int

    items: list[
        SpacedPracticeItem
    ]


class StudyPlanResponse(BaseModel):
    subject_id: int
    subject_name: str

    generated_at: datetime

    horizon_days: int

    algorithm: str

    total_topics: int

    scheduled_topics: int

    due_topics: int

    deferred_topics: int

    days: list[
        StudyPlanDay
    ]