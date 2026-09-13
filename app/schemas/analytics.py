from __future__ import annotations

from datetime import datetime
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