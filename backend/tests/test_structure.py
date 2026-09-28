import os
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough")

from app.db.models import Base
from app.main import app


def test_orm_table_count_matches_schema():
    assert len(Base.metadata.tables) == 45


def test_openapi_is_generated():
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert "/api/v1/auth/register" in schema["paths"]
    assert "/api/v1/chat/conversations/{conversation_id}/ask" in schema["paths"]
