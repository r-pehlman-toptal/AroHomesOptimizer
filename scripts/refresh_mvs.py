#!/usr/bin/env python3
"""
Refresh analytics materialized views in dependency order.
Uses DATABASE_URL or DB_URL. Supports REFRESH CONCURRENTLY and optional grid repopulation.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Install psycopg2: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)


def get_conn():
    url = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL")
    if not url:
        print("Set DATABASE_URL or DB_URL", file=sys.stderr)
        sys.exit(1)
    # Accept postgresql+psycopg2:// or postgresql://
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(url)


def run_refresh(conn, mv_name: str, concurrently: bool) -> float:
    con = "CONCURRENTLY " if concurrently else ""
    q = f"REFRESH MATERIALIZED VIEW {con}analytics.{mv_name}"
    start = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(q)
    conn.commit()
    return time.perf_counter() - start


def run_sql_file(conn, path: Path) -> float:
    start = time.perf_counter()
    with open(path, encoding="utf-8") as f:
        body = f.read()
    with conn.cursor() as cur:
        cur.execute(body)
    conn.commit()
    return time.perf_counter() - start


def main():
    ap = argparse.ArgumentParser(description="Refresh analytics MVs in dependency order")
    ap.add_argument("--concurrently", type=lambda x: x.lower() == "true", default=True,
                    help="Use REFRESH MATERIALIZED VIEW CONCURRENTLY (default: true)")
    ap.add_argument("--refresh-grid", action="store_true",
                    help="After fact MV, repopulate analytics.grid_cells_025 (run 041)")
    ap.add_argument("--sql-dir", type=Path, default=Path(__file__).resolve().parent.parent / "sql",
                    help="Directory containing 041_populate_grid_cells_025.sql")
    args = ap.parse_args()

    conn = get_conn()
    sql_dir = args.sql_dir
    total_start = time.perf_counter()

    # 1) Fact MV
    t = run_refresh(conn, "mv_sale_la_since2020_ppsf400", args.concurrently)
    print(f"mv_sale_la_since2020_ppsf400: {t:.2f}s")

    # 2) Optional: repopulate grid from new extent
    if args.refresh_grid:
        path_041 = sql_dir / "041_populate_grid_cells_025.sql"
        if path_041.exists():
            t = run_sql_file(conn, path_041)
            print(f"populate grid_cells_025: {t:.2f}s")
        else:
            print(f"skip grid (file not found: {path_041})", file=sys.stderr)

    # 3) City x year
    t = run_refresh(conn, "mv_agg_city_year_metrics", args.concurrently)
    print(f"mv_agg_city_year_metrics: {t:.2f}s")

    # 4) Grid x year
    t = run_refresh(conn, "mv_agg_grid_year_ppsf_025", args.concurrently)
    print(f"mv_agg_grid_year_ppsf_025: {t:.2f}s")

    conn.close()
    print(f"total: {time.perf_counter() - total_start:.2f}s")


if __name__ == "__main__":
    main()
