from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.db import QueryRunner


@dataclass
class GoldBuilder:
    """
    Build canonical 'gold' tables/views from raw or staging schemas.

    This is where the Principal DS can encode:
    - De‑duplication logic.
    - Canonical join keys across assessor, MLS, zoning, and geometry.
    - Business rules for which records to keep/drop.
    """

    sql_root: Path
    runner: QueryRunner

    @property
    def gold_dir(self) -> Path:
        return self.sql_root / "gold"

    def build_all(self) -> None:
        """
        Execute all SQL files in `sql/gold` in a deterministic order.
        """
        sql_files = sorted(self.gold_dir.glob("*.sql"))
        self._run_files(sql_files)

    def _run_files(self, files: Iterable[Path]) -> None:
        self.runner.run_many_files(files)

