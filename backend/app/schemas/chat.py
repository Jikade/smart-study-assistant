from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ConversationCreate(BaseModel):
    subject_id: int | None = None
    title: str | None = Field(default=None, max_length=300)
    document_ids: list[int] = []


class ConversationOut(ORMModel):
    id: int
    user_id: int
    subject_id: int | None = None
    title: str | None = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    input_mode: str = Field(default="TEXT", pattern="^(TEXT|VOICE)$")
    top_k: int | None = Field(default=None, ge=1, le=20)


class CitationOut(BaseModel):
    chunk_id: int
    document_id: int
    rank_order: int
    similarity_score: float | None = None
    excerpt: str


class ChatAnswer(BaseModel):
    user_message_id: int
    assistant_message_id: int
    answer: str
    model_name: str | None = None
    citations: list[CitationOut]


class MessageOut(ORMModel):
    id: int
    conversation_id: int
    role: str
    content: str
    input_mode: str
    model_name: str | None = None
    created_at: datetime
