#!/usr/bin/env python3
"""
Apply gold-layer views (parcel_gold, transaction_gold, optionally city_year).
Run from project root with DB_URL or DATABASE_URL set in .env or environment.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent.parent
    load_dotenv(_root / ".env")
except ImportError:
    pass

try:
    import psycopg2
except ImportError:
    print("Install psycopg2: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)


def get_conn():
    url = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL")
    if not url:
        print("Set DATABASE_URL or DB_URL in .env or environment", file=sys.stderr)
        sys.exit(1)
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(url)


def run_sql_file(conn, path: Path) -> float:
    start = time.perf_counter()
    with open(path, encoding="utf-8") as f:
        body = f.read()
    with conn.cursor() as cur:
        cur.execute(body)
    conn.commit()
    return time.perf_counter() - start


def main():
    root = Path(__file__).resolve().parent.parent
    sql_dir = root / "sql" / "gold"
    agg_dir = root / "sql" / "agg"

    conn = get_conn()
    total_start = time.perf_counter()

    # 1) parcel_gold
    path = sql_dir / "parcel_gold.sql"
    if not path.exists():
        print(f"Not found: {path}", file=sys.stderr)
        sys.exit(1)
    t = run_sql_file(conn, path)
    print(f"parcel_gold: {t:.2f}s")

    # 2) transaction_gold
    path = sql_dir / "transaction_gold.sql"
    if not path.exists():
        print(f"Not found: {path}", file=sys.stderr)
        sys.exit(1)
    t = run_sql_file(conn, path)
    print(f"transaction_gold: {t:.2f}s")

    # 3) Optional: city_year (depends on parcel_gold, transaction_gold)
    path = agg_dir / "city_year.sql"
    if path.exists():
        t = run_sql_file(conn, path)
        print(f"city_year: {t:.2f}s")
    else:
        print("city_year: skip (file not found)")

    # 4) Optional: grid_year (depends on analytics schema: mv_agg_grid_year_ppsf_025, grid_cells_025)
    path = agg_dir / "grid_year.sql"
    if path.exists():
        try:
            t = run_sql_file(conn, path)
            print(f"grid_year: {t:.2f}s")
        except Exception as e:
            print(f"grid_year: skip ({e})")

    conn.close()
    print(f"total: {time.perf_counter() - total_start:.2f}s")


if __name__ == "__main__":
    main()
