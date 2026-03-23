#!/usr/bin/env python3
"""
Build feasibility constraints table for a subset of LA parcels.

Loads parcel_gold and property_zoning + zone from the DB, runs ZoningConstraintBuilder,
and writes a constraints CSV. Run from project root with DB_URL set.

Usage:
  python scripts/build_constraints.py [--limit N] [--output PATH]
  --limit   Max parcels to load (default 50_000); 0 = no limit.
  --output  Output CSV path (default output/constraints_la_subset.csv).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow importing from src when run from project root.
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
except ImportError:
    pass

import pandas as pd

from src.db.connection import get_engine
from src.feasibility.zoning_constraints import ZoningConstraintBuilder


def load_parcels(engine, limit: int) -> pd.DataFrame:
    """Load parcel_gold, LA only. Optional limit for subset."""
    sql = """
    SELECT parcel_id, street_id, zip_code, city_id, city_name, county,
           lot_size_sq_ft, year_built
    FROM parcel_gold
    WHERE UPPER(TRIM(city_name)) = 'LOS ANGELES'
    """
    if limit > 0:
        sql += f" LIMIT {int(limit)}"
    return pd.read_sql(sql, engine)


def load_zoning(engine, parcel_ids: pd.Series | None) -> pd.DataFrame:
    """Load one zone per parcel from property_zoning + zone."""
    sql = """
    SELECT pz.property_id AS parcel_id, z.name AS zone_code
    FROM property_zoning pz
    JOIN zone z ON z.id = pz.zone_id
    """
    if parcel_ids is not None and len(parcel_ids) > 0:
        ids = parcel_ids.dropna().astype(int).unique().tolist()
        if ids:
            placeholders = ",".join(str(i) for i in ids)
            sql += f" WHERE pz.property_id IN ({placeholders})"
    return pd.read_sql(sql, engine)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build constraints table for LA subset.")
    parser.add_argument("--limit", type=int, default=50_000, help="Max parcels (0 = no limit)")
    parser.add_argument("--output", type=Path, default=_root / "output" / "constraints_la_subset.csv")
    args = parser.parse_args()

    try:
        engine = get_engine()
    except RuntimeError as e:
        print(f"DB not configured: {e}", file=sys.stderr)
        return 1

    print("Loading parcels (LA)...")
    parcels = load_parcels(engine, args.limit)
    if parcels.empty:
        print("No LA parcels in parcel_gold. Apply gold views first (scripts/apply_gold.py).", file=sys.stderr)
        return 1
    print(f"  Loaded {len(parcels):,} parcels")

    print("Loading zoning...")
    zoning = load_zoning(engine, parcels["parcel_id"])
    print(f"  Loaded {len(zoning):,} parcel–zone rows")

    builder = ZoningConstraintBuilder()
    constraints = builder.build_constraints(parcels, zoning, geom=None)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    constraints.to_csv(args.output, index=False)
    print(f"Wrote {len(constraints):,} rows to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
