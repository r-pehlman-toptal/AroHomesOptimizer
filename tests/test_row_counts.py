from pathlib import Path

import pytest
from sqlalchemy import text

from src.db import QueryRunner


@pytest.mark.skip(reason="Requires configured database with staging and gold tables.")
def test_parcel_row_counts_nonzero():
    """
    Basic sanity check: parcel_gold should not be empty once ETL is wired up.
    """
    runner = QueryRunner.from_env()
    res = runner.run_sql("SELECT COUNT(*) AS c FROM parcel_gold;")
    count = res.scalar_one()
    assert count > 0


@pytest.mark.skip(reason="Requires configured database with staging and gold tables.")
def test_transaction_unique_ids():
    """
    Example duplication check for transaction_gold.
    """
    runner = QueryRunner.from_env()
    res = runner.run_sql(
        """
        SELECT COUNT(*) AS c, COUNT(DISTINCT transaction_id) AS u
        FROM transaction_gold;
        """
    )
    row = res.mappings().one()
    assert row["c"] == row["u"]

