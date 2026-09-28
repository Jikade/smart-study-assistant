from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class DocumentOut(ORMModel):
    id: int
    owner_id: int
    subject_id: int | None = None
    original_name: str
    stored_name: str | None = None
    storage_url: str | None = None
    mime_type: str | None = None
    file_extension: str | None = None
    file_size_bytes: int | None = None
    page_count: int | None = None
    status: str
    visibility: str
    processing_error: str | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChunkOut(ORMModel):
    id: int
    document_id: int
    section_id: int | None = None
    chunk_index: int
    content: str
    token_count: int | None = None
    char_count: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    created_at: datetime


class ProcessDocumentResponse(BaseModel):
    document_id: int
    status: str
    chunks_created: int
    embeddings_created: int

class EmbedDocumentResponse(BaseModel):
    document_id: int
    chunks_total: int
    embeddings_created: int
    embedding_model: str
