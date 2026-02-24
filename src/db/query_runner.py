from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine, Result

from .connection import get_engine
from .sql_loader import load_sql


@dataclass
class QueryRunner:
    """
    Lightweight query helper.

    Used to:
    - Execute parameterized SQL from strings or files.
    - Materialize gold and aggregate tables.
    - Run ad‑hoc decision‑oriented queries for stakeholders.
    """

    engine: Engine

    @classmethod
    def from_env(cls, echo: bool = False) -> "QueryRunner":
        return cls(engine=get_engine(echo=echo))

    def run_sql(
        self,
        sql: str,
        params: Optional[Mapping[str, Any]] = None,
    ) -> Result:
        with self.engine.begin() as conn:
            return conn.execute(text(sql), params or {})

    def run_sql_file(
        self,
        path: Path,
        params: Optional[Mapping[str, Any]] = None,
    ) -> Result:
        sql = load_sql(path)
        return self.run_sql(sql, params=params)

    def run_many_files(
        self,
        paths: Iterable[Path],
    ) -> None:
        """
        Execute a list of SQL files in order, typically used for:
        - gold layer materialization
        - aggregate layer builds
        """
        for path in paths:
            self.run_sql_file(path)

