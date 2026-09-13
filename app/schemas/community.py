from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel


class CommunityPostCreate(BaseModel):
    quiz_id: int | None = None
    flashcard_deck_id: int | None = None
    title: str | None = Field(default=None, max_length=300)
    description: str | None = None

    @model_validator(mode="after")
    def one_resource(self):
        if (self.quiz_id is None) == (self.flashcard_deck_id is None):
            raise ValueError("Provide exactly one of quiz_id or flashcard_deck_id")
        return self


class CommunityPostOut(ORMModel):
    id: int
    owner_id: int
    quiz_id: int | None = None
    flashcard_deck_id: int | None = None
    title: str | None = None
    description: str | None = None
    status: str
    published_at: datetime
    created_at: datetime
