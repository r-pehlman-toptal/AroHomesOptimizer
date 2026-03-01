"""
Row-count and uniqueness checks for gold views (parcel_gold, transaction_gold).

Run with: pytest tests/test_row_counts.py -v
Tests run when DB_URL is set and gold views exist; skip with a clear reason if DB is unavailable.
"""
from pathlib import Path

import pytest
from sqlalchemy import text

from src.db import QueryRunner


def _get_runner():
    """Build QueryRunner from env; skip if DB_URL not set or connection fails."""
    try:
        return QueryRunner.from_env()
    except Exception:
        pytest.skip("DB_URL not configured or connection failed")


def test_parcel_gold_row_count_nonzero():
    """parcel_gold should have at least one row once gold SQL has been applied."""
    runner = _get_runner()
    res = runner.run_sql("SELECT COUNT(*) AS c FROM parcel_gold;")
    count = res.scalars().one()
    assert count > 0, "parcel_gold is empty; run sql/gold/parcel_gold.sql"


def test_parcel_gold_unique_parcel_id():
    """parcel_gold must have one row per parcel_id (no duplicates)."""
    runner = _get_runner()
    res = runner.run_sql(
        """
        SELECT COUNT(*) AS total, COUNT(DISTINCT parcel_id) AS distinct_ids
        FROM parcel_gold;
        """
    )
    row = res.mappings().one()
    assert row["total"] == row["distinct_ids"], (
        f"parcel_gold duplicate parcel_id: total={row['total']} distinct={row['distinct_ids']}"
    )


def test_transaction_gold_unique_transaction_id():
    """transaction_gold must have one row per transaction_id (no duplicates)."""
    runner = _get_runner()
    res = runner.run_sql(
        """
        SELECT COUNT(*) AS c, COUNT(DISTINCT transaction_id) AS u
        FROM transaction_gold;
        """
    )
    row = res.mappings().one()
    assert row["c"] == row["u"], (
        f"transaction_gold duplicate transaction_id: count={row['c']} distinct={row['u']}"
    )


def test_transaction_gold_parcel_id_foreign_key():
    """Every transaction_gold.parcel_id should exist in parcel_gold (referential consistency)."""
    runner = _get_runner()
    res = runner.run_sql(
        """
        SELECT COUNT(*) AS orphan_count
        FROM transaction_gold t
        LEFT JOIN parcel_gold p ON p.parcel_id = t.parcel_id
        WHERE p.parcel_id IS NULL;
        """
    )
    orphan_count = res.scalars().one()
    assert orphan_count == 0, (
        f"transaction_gold has {orphan_count} rows with parcel_id not in parcel_gold"
    )
