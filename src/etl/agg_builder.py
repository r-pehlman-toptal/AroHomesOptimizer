from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.db import QueryRunner


@dataclass
class AggregateBuilder:
    """
    Build aggregate tables/views such as city_year, submarket_year, grid_year, etc.

    These tables support:
    - Scenario and sensitivity analysis across LA submarkets.
    - Visualization of submarket performance for non‑technical stakeholders.
    """

    sql_root: Path
    runner: QueryRunner

    @property
    def agg_dir(self) -> Path:
        return self.sql_root / "agg"

    def build_all(self) -> None:
        sql_files = sorted(self.agg_dir.glob("*.sql"))
        self._run_files(sql_files)

    def _run_files(self, files: Iterable[Path]) -> None:
        self.runner.run_many_files(files)

