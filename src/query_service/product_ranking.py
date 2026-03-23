"""
Rebuild decision system: product → where to build. Ranks ZIPs (or cities) by PPSF/DOM/supply.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from sqlalchemy import text
from sqlalchemy.engine import Connection

from src.db import load_sql
from src.query_service import queries
from src.query_service.schemas import (
    AreaRankingRow,
    ProductWhereToBuildParams,
    VolumeByZipYearParams,
)


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PARCEL_SUPPLY_BY_ZIP_SQL = _PROJECT_ROOT / "sql" / "readonly" / "parcel_supply_by_zip.sql"


def _min_lot_dimension_for_sqft(sqft: float) -> float:
    from math import sqrt
    buildable = sqft
    min_side = sqrt(buildable / 2.0)
    return round(min_side * 1.15, 1)


def product_areas_ranking(conn: Connection, p: ProductWhereToBuildParams) -> List[AreaRankingRow]:
    """
    Rank areas (ZIPs or cities) for a target product: median PPSF, DOM, supply count, composite score.
    """
    city = (p.city_name or "LOS ANGELES").strip().upper()
    min_dim = _min_lot_dimension_for_sqft(p.target_sqft)
    min_lot_sq_ft = max(p.target_sqft * 2.0, min_dim * min_dim)  # FAR ~0.5 and shape

    if p.geography == "city":
        return _rank_cities(conn, p, city)
    return _rank_zips(conn, p, city, min_dim, min_lot_sq_ft)


def _rank_zips(
    conn: Connection,
    p: ProductWhereToBuildParams,
    city: str,
    min_dim: float,
    min_lot_sq_ft: float,
) -> List[AreaRankingRow]:
    vol_params = VolumeByZipYearParams(min_sold_date="2020-01-01", zip_code=None, city_name=city)
    zip_rows = queries.volume_by_zip_year(conn, vol_params)
    # Use latest year with data
    years = sorted(set(r.sale_year for r in zip_rows), reverse=True)
    year = years[0] if years else 2024
    by_zip = {r.zip_code: r for r in zip_rows if r.sale_year == year and r.sale_count >= p.min_comp_count}

    supply_sql = load_sql(_PARCEL_SUPPLY_BY_ZIP_SQL)
    supply_params = {
        "min_width_ft": min_dim,
        "min_depth_ft": min_dim,
        "min_lot_sq_ft": min_lot_sq_ft,
        "city_name": city,
    }
    result = conn.execute(text(supply_sql), supply_params)
    supply_map = {row["geo_id"]: int(row["supply_count"]) for row in result.mappings()}

    rows: List[AreaRankingRow] = []
    ppsfs = [r.median_ppsf for r in by_zip.values() if r.median_ppsf is not None]
    doms = [r.median_dom for r in by_zip.values() if r.median_dom is not None]
    supplies = [supply_map.get(z, 0) for z in by_zip]
    max_ppsf = max(ppsfs) if ppsfs else 1
    max_dom = max(doms) if doms else 1
    max_supply = max(supplies) if supplies else 1
    for zip_code, vol in by_zip.items():
        supply = supply_map.get(zip_code, 0)
        score_ppsf = (vol.median_ppsf or 0) / max_ppsf if max_ppsf else 0
        score_dom = 1 - (vol.median_dom or 0) / max_dom if max_dom else 0
        score_supply = supply / max_supply if max_supply else 0
        score = 0.4 * score_ppsf + 0.3 * score_dom + 0.3 * score_supply
        band = "high" if (vol.sale_count or 0) >= 50 else ("med" if (vol.sale_count or 0) >= 20 else "low")
        expl = f"PPSF ${int(vol.median_ppsf or 0):,}, DOM {int(vol.median_dom or 0)}, {supply} lots"
        rows.append(
            AreaRankingRow(
                geo_id=zip_code,
                geo_type="zip",
                median_ppsf=vol.median_ppsf,
                median_dom=vol.median_dom,
                comp_count=vol.sale_count or 0,
                confidence_band=band,
                supply_count=supply,
                score=round(score, 4),
                explanation=expl,
            )
        )
    rows.sort(key=lambda r: (r.score or 0), reverse=True)
    return rows[: p.limit]


_SUBMARKET_CITIES = [
    "LOS ANGELES", "BURBANK", "GLENDALE", "PASADENA", "SANTA MONICA",
    "LONG BEACH", "INGLEWOOD", "CULVER CITY", "WEST HOLLYWOOD", "SAN FERNANDO",
]


def _rank_cities(conn: Connection, p: ProductWhereToBuildParams, city: str) -> List[AreaRankingRow]:
    from src.query_service.schemas import VolumeByCityYearParams
    by_city = {}
    for cname in _SUBMARKET_CITIES:
        city_params = VolumeByCityYearParams(min_sold_date="2020-01-01", city_name=cname)
        city_rows = queries.volume_by_city_year(conn, city_params)
        if not city_rows:
            continue
        years = sorted(set(r.sale_year for r in city_rows), reverse=True)
        year = years[0] if years else 2024
        for r in city_rows:
            if r.sale_year == year and (r.total_sales or 0) >= p.min_comp_count:
                by_city[r.city_name] = r
                break
    rows = []
    for cname, vol in by_city.items():
        band = "high" if (vol.total_sales or 0) >= 50 else ("med" if (vol.total_sales or 0) >= 20 else "low")
        rows.append(
            AreaRankingRow(
                geo_id=cname,
                geo_type="city",
                median_ppsf=vol.median_ppsf,
                median_dom=None,
                comp_count=vol.total_sales or 0,
                confidence_band=band,
                supply_count=None,
                score=None,
                explanation=f"PPSF ${int(vol.median_ppsf or 0):,}, {vol.total_sales or 0} sales",
            )
        )
    rows.sort(key=lambda r: (r.median_ppsf or 0), reverse=True)
    return rows[: p.limit]
