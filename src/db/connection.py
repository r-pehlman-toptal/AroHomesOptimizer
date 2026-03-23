import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

# Load .env from project root (parent of src/) so it works regardless of cwd.
_project_root = Path(__file__).resolve().parent.parent.parent  # src/db -> src -> repo root
load_dotenv(_project_root / ".env")


def _get_db_url(explicit_url: Optional[str] = None) -> str:
    """
    Resolve the database URL from (in order of precedence):
    1. explicit_url argument
    2. DB_URL environment variable

    Raises:
        RuntimeError: if no URL is provided.
    """
    url = explicit_url or os.getenv("DB_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "Database URL not configured. Set DB_URL env var or pass explicit_url."
        )
    return url


def get_engine(url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    Create a SQLAlchemy Engine for the configured database.
    """
    db_url = _get_db_url(url)
    return create_engine(db_url, echo=echo, future=True)


def get_sessionmaker(url: Optional[str] = None, echo: bool = False) -> sessionmaker[Session]:
    """
    Convenience wrapper to create a session factory bound to the engine.
    """
    engine = get_engine(url=url, echo=echo)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

