from sqlalchemy import text

from app.db.session import engine

with engine.connect() as conn:
    version = conn.execute(text("SELECT version()" )).scalar_one()
    tables = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'" )).scalar_one()
    vector = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')" )).scalar_one()
    print(version)
    print(f"public tables: {tables}")
    print(f"pgvector enabled: {vector}")
