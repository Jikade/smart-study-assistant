from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ocr_enabled: bool = Field(True, alias="OCR_ENABLED")
    ocr_languages: str = Field("vie+eng", alias="OCR_LANGUAGES")
    ocr_dpi: int = Field(200, alias="OCR_DPI")
    ocr_page_min_chars: int = Field(30, alias="OCR_PAGE_MIN_CHARS")
    tessdata_dir: str | None = Field(None, alias="TESSDATA_DIR")

    app_name: str = Field("Smart Study Assistant API", alias="APP_NAME")
    environment: Literal["development", "test", "production"] = Field("development", alias="ENVIRONMENT")
    debug: bool = Field(True, alias="DEBUG")
    api_v1_prefix: str = Field("/api/v1", alias="API_V1_PREFIX")

    database_url: str = Field(
        "postgresql+psycopg://postgres:postgres@localhost:5432/smart_study_assistant",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field("CHANGE_ME", alias="JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(30, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"], alias="CORS_ORIGINS")

    storage_dir: Path = Field(Path("./storage/uploads"), alias="STORAGE_DIR")
    max_upload_mb: int = Field(30, alias="MAX_UPLOAD_MB")
    chunk_size_chars: int = Field(1800, alias="CHUNK_SIZE_CHARS")
    chunk_overlap_chars: int = Field(250, alias="CHUNK_OVERLAP_CHARS")

    rag_top_k: int = Field(5, alias="RAG_TOP_K")
    rag_min_score: float = Field(0.05, alias="RAG_MIN_SCORE")

    ai_provider: Literal["disabled", "openai_compatible"] = Field("disabled", alias="AI_PROVIDER")
    ai_base_url: str = Field("http://localhost:11434/v1", alias="AI_BASE_URL")
    ai_api_key: str | None = Field(None, alias="AI_API_KEY")
    ai_chat_model: str | None = Field(None, alias="AI_CHAT_MODEL")
    ai_embedding_model: str | None = Field(None, alias="AI_EMBEDDING_MODEL")
    ai_timeout_seconds: float = Field(60.0, alias="AI_TIMEOUT_SECONDS")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
