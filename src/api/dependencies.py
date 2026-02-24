from __future__ import annotations

from typing import Iterator
import logging

from fastapi import Depends
from sqlalchemy.engine import Connection

from src.db import get_engine


logger = logging.getLogger("la_api.db")


def db_connection_dependency() -> Iterator[Connection]:
    """
    FastAPI dependency that yields a live DB connection for the duration
    of the request and closes it afterwards.
    """
    engine = get_engine()
    conn = engine.connect()
    logger.debug("Opened DB connection")
    try:
        yield conn
    finally:
        logger.debug("Closing DB connection")
        conn.close()


def cognito_auth_dependency() -> None:
    """
    Placeholder for Cognito JWT verification.

    For now this is a no-op; in production, implement:
    - JWT extraction from Authorization header.
    - JWKS fetching/caching and signature verification.
    - Audience / issuer checks.
    """
    return None

