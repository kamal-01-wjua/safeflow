import os
from sqlalchemy import create_engine
from sqlmodel import Session

def _db_url() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("SAFEFLOW_DB_URL")
    if not url:
        raise RuntimeError("Missing DATABASE_URL / SAFEFLOW_DB_URL")
    return url

engine = create_engine(_db_url(), pool_pre_ping=True)

def get_session():
    with Session(engine) as session:
        yield session
