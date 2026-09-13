from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class FlashcardCreate(BaseModel):
    front_text: str = Field(min_length=1)
    back_text: str = Field(min_length=1)
    hint: str | None = None
    source_chunk_id: int | None = None


class DeckCreate(BaseModel):
    subject_id: int | None = None
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    visibility: str = Field(default="PRIVATE", pattern="^(PRIVATE|UNLISTED|PUBLIC)$")
    document_ids: list[int] = []
    cards: list[FlashcardCreate] = []


class DeckGenerateRequest(BaseModel):
    subject_id: int | None = None
    title: str = Field(min_length=1, max_length=300)
    document_ids: list[int] = []
    card_count: int = Field(default=20, ge=1, le=100)


class DeckOut(ORMModel):
    id: int
    owner_id: int
    subject_id: int | None = None
    source_deck_id: int | None = None
    title: str
    description: str | None = None
    generation_mode: str
    visibility: str
    status: str
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class FlashcardOut(ORMModel):
    id: int
    deck_id: int
    source_chunk_id: int | None = None
    front_text: str
    back_text: str
    hint: str | None = None
    card_order: int
    created_at: datetime


class ReviewRequest(BaseModel):
    rating: int = Field(ge=0, le=3, description="0=Again, 1=Hard, 2=Good, 3=Easy")
    response_time_ms: int | None = Field(default=None, ge=0)


class ProgressOut(ORMModel):
    user_id: int
    flashcard_id: int
    repetitions: int
    interval_days: int
    ease_factor: Decimal
    lapse_count: int
    last_rating: int | None = None
    last_reviewed_at: datetime | None = None
    next_review_at: datetime
