from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    color_hex: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    color_hex: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_archived: bool | None = None


class SubjectOut(ORMModel):
    id: int
    owner_id: int
    name: str
    description: str | None = None
    color_hex: str | None = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
