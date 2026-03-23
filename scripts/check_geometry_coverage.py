#!/usr/bin/env python3
"""
Compute geometry coverage stats for parcel_gold: total parcels, valid center_point count, SRID.

Run from project root with DB_URL set. Prints a short summary; optionally write to notes/geometry-coverage-note.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
except ImportError:
    pass

from sqlalchemy import text

from src.db.connection import get_engine


def main() -> int:
    try:
        engine = get_engine()
    except RuntimeError as e:
        print(f"DB not configured: {e}", file=sys.stderr)
        return 1

    with engine.connect() as conn:
        # Total parcels in parcel_gold
        r = conn.execute(text("SELECT COUNT(*) AS n FROM parcel_gold"))
        total = r.scalar()

        # With non-NULL center_point
        r = conn.execute(text("""
            SELECT COUNT(*) AS n FROM parcel_gold
            WHERE center_point_4326 IS NOT NULL
        """))
        with_geom = r.scalar()

        # Valid (ST_IsValid) center_point
        r = conn.execute(text("""
            SELECT COUNT(*) AS n FROM parcel_gold
            WHERE center_point_4326 IS NOT NULL
              AND ST_IsValid(center_point_4326::geometry)
        """))
        valid = r.scalar()

        # Distinct SRIDs
        r = conn.execute(text("""
            SELECT DISTINCT ST_SRID(center_point_4326::geometry) AS srid
            FROM parcel_gold
            WHERE center_point_4326 IS NOT NULL
        """))
        srids = [row[0] for row in r]

    pct = (valid / total * 100) if total else 0
    print("Geometry coverage (parcel_gold)")
    print("  Total parcels:        ", total)
    print("  With center_point:    ", with_geom)
    print("  Valid center_point:   ", valid)
    print("  Coverage % (valid):   ", f"{pct:.1f}%")
    print("  SRIDs seen:           ", srids if srids else "N/A")

    return 0


if __name__ == "__main__":
    sys.exit(main())
