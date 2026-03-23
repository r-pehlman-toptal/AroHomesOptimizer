from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection

from src.db import load_sql
from src.query_service.schemas import (
    BedBathDistributionParams,
    BedBathDistributionRow,
    PrincipalZoneParams,
    PrincipalZoneRow,
    LotSizeBucketsParams,
    LotSizeBucketRow,
    RankedZipsParams,
    RankedZipRow,
    F1CompsParams,
    F1CompsRow,
    F3OfferRangeParams,
    F3OfferRangeRow,
    F4OverpayRiskParams,
    F4OverpayRiskRow,
    CompsAggregateParams,
    CompsAggregateRow,
    CompsAggregateCompRow,
    ZoningSummaryParams,
    ZoningSummaryRow,
    ParcelCenterParams,
    ParcelCenterRow,
    ParcelFootprintParams,
    ParcelFootprintRow,
    PropertyInfoParams,
    PropertyInfoRow,
    NearbyZoningParams,
    NearbyZoningRow,
    CompsParams,
    CompsRow,
    PpsfMapParams,
    PpsfMapRow,
    OfferRangeParams,
    OfferRangeRow,
    OverpayRiskParams,
    OverpayRiskRow,
    ConfidenceCoverageParams,
    ConfidenceCoverageRow,
    VolumeByZipYearParams,
    VolumeByZipYearRow,
    VolumeByCityYearParams,
    VolumeByCityYearRow,
    VolumeByZipMonthParams,
    VolumeByZipMonthRow,
)
from src.query_service.comps_confidence import confidence_score_and_band, confidence_components


def _fetch_all(conn: Connection, sql: str, params: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    result = conn.execute(text(sql), params)
    for row in result.mappings():
        yield dict(row)


def bed_bath_distribution(conn: Connection, p: BedBathDistributionParams) -> List[BedBathDistributionRow]:
    """
    Query A: LA Bed/Bath distribution with fixed SFR filters and robust joins.
    """
    sql = """
    WITH address_uniq AS (
        SELECT
            pa.property_id,
            MIN(pa.street_id) AS street_id,
            MIN(pa.zip_code) AS zip_code
        FROM property_address AS pa
        GROUP BY pa.property_id
    ),
    city_lookup AS (
        SELECT
            s.id AS street_id,
            UPPER(c.name) AS city_name
        FROM street AS s
        JOIN city AS c
          ON s.city_id = c.id
    ),
    base AS (
        SELECT
            h.property_id,
            h.sold_price,
            h.sold_date,
            h.living_sq_ft,
            h.bedrooms_total AS beds,
            h.bathrooms_full AS baths_full,
            h.bathrooms_half AS baths_half,
            CASE
                WHEN h.living_sq_ft > 0 THEN h.sold_price::numeric / h.living_sq_ft
                ELSE NULL
            END AS price_per_sqft
        FROM mls_history AS h
        JOIN address_uniq AS pa
          ON h.property_id = pa.property_id
        JOIN city_lookup AS cl
          ON pa.street_id = cl.street_id
        WHERE
            cl.city_name = :city
            AND h.property_use_standardized = :property_use
            AND h.sold_date >= :min_sold_date
            AND h.year_built > :min_year_built
            AND h.sold_price > 0
            AND h.living_sq_ft > 0
            AND h.sold_date IS NOT NULL
            AND h.bedrooms_total BETWEEN :min_beds AND :max_beds
            AND h.bathrooms_full BETWEEN :min_full_baths AND :max_full_baths
            AND h.bathrooms_half = ANY(:allowed_half_baths)
            AND h.living_sq_ft BETWEEN :min_living_sqft AND :max_living_sqft
    ),
    filtered AS (
        SELECT *
        FROM base
        WHERE price_per_sqft >= :min_ppsf
    )
    SELECT
        FLOOR(f.living_sq_ft / 100.0)::int * 100 AS living_sqft_bucket,
        f.beds,
        f.baths_full,
        f.baths_half,
        COUNT(*) AS sale_count,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.price_per_sqft) AS median_price_per_sqft,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.sold_price) AS median_sold_price
    FROM filtered AS f
    GROUP BY
        living_sqft_bucket,
        f.beds,
        f.baths_full,
        f.baths_half
    ORDER BY
        living_sqft_bucket,
        f.beds,
        f.baths_full,
        f.baths_half;
    """

    params = {
        "city": p.city,
        "property_use": p.property_use,
        "min_sold_date": p.min_sold_date,
        "min_year_built": p.min_year_built,
        "min_ppsf": p.min_ppsf,
        "min_living_sqft": p.min_living_sqft,
        "max_living_sqft": p.max_living_sqft,
        "min_beds": p.min_beds,
        "max_beds": p.max_beds,
        "min_full_baths": p.min_full_baths,
        "max_full_baths": p.max_full_baths,
        "allowed_half_baths": p.allowed_half_baths,
    }

    rows = [BedBathDistributionRow(**r) for r in _fetch_all(conn, sql, params)]
    return rows


def principal_sfr_zone(conn: Connection, p: PrincipalZoneParams) -> List[PrincipalZoneRow]:
    """
    Query B: Principal detached-SFR zone per city (by parcel count).
    """
    sql = """
    WITH address_uniq AS (
        SELECT
            pa.property_id,
            MIN(pa.street_id) AS street_id
        FROM property_address AS pa
        GROUP BY pa.property_id
    ),
    city_lookup AS (
        SELECT
            s.id AS street_id,
            UPPER(c.name) AS city_name
        FROM street AS s
        JOIN city AS c
          ON s.city_id = c.id
    ),
    zoning AS (
        SELECT
            pz.property_id,
            z.name AS zoning_code
        FROM property_zoning AS pz
        JOIN zone AS z
          ON pz.zone_id = z.id
        WHERE
            z.name ILIKE '%R1%' OR
            z.name ILIKE '%RS%' OR
            z.name ILIKE '%RE%'
    ),
    joined AS (
        SELECT
            cl.city_name,
            zn.zoning_code,
            pa.property_id
        FROM zoning AS zn
        JOIN address_uniq AS pa
          ON zn.property_id = pa.property_id
        JOIN city_lookup AS cl
          ON pa.street_id = cl.street_id
        WHERE cl.city_name = ANY(:cities)
    ),
    zone_counts AS (
        SELECT
            city_name,
            zoning_code,
            COUNT(DISTINCT property_id) AS parcel_count
        FROM joined
        GROUP BY city_name, zoning_code
    ),
    ranked AS (
        SELECT
            city_name,
            zoning_code,
            parcel_count,
            ROW_NUMBER() OVER (PARTITION BY city_name ORDER BY parcel_count DESC) AS rn
        FROM zone_counts
        WHERE parcel_count >= :min_parcels
    )
    SELECT
        city_name,
        zoning_code,
        parcel_count
    FROM ranked
    WHERE rn = 1
    ORDER BY city_name;
    """

    params = {
        "cities": p.cities,
        "min_parcels": p.min_parcels,
    }
    rows = [PrincipalZoneRow(**r) for r in _fetch_all(conn, sql, params)]
    return rows


def lot_size_buckets(conn: Connection, p: LotSizeBucketsParams) -> List[LotSizeBucketRow]:
    """
    Query C: Lot size width/depth bucket counts by ZIP.
    Optional filters: property_subtype, min/max lot_size_sq_ft, exclude_outliers (10–250 ft).
    """
    sql = """
    WITH address_uniq AS (
        SELECT
            pa.property_id,
            MIN(pa.zip_code) AS zip_code,
            MIN(pa.street_id) AS street_id
        FROM property_address AS pa
        GROUP BY pa.property_id
    ),
    geom AS (
        SELECT
            pg.property_id,
            pg.vendor_lot_width_ft,
            pg.vendor_lot_depth_ft,
            pg.lot_size_sq_ft
        FROM property_geometry AS pg
        WHERE
            pg.vendor_lot_width_ft IS NOT NULL
            AND pg.vendor_lot_depth_ft IS NOT NULL
            AND pg.vendor_lot_width_ft > 0
            AND pg.vendor_lot_depth_ft > 0
            AND (:exclude_outliers = FALSE OR (pg.vendor_lot_width_ft BETWEEN 10 AND 250 AND pg.vendor_lot_depth_ft BETWEEN 10 AND 250))
            AND (:min_lot_size_sq_ft IS NULL OR COALESCE(pg.lot_size_sq_ft, pg.vendor_lot_width_ft * pg.vendor_lot_depth_ft) >= :min_lot_size_sq_ft)
            AND (:max_lot_size_sq_ft IS NULL OR COALESCE(pg.lot_size_sq_ft, pg.vendor_lot_width_ft * pg.vendor_lot_depth_ft) <= :max_lot_size_sq_ft)
    ),
    joined AS (
        SELECT
            a.zip_code,
            g.vendor_lot_width_ft,
            g.vendor_lot_depth_ft
        FROM geom AS g
        JOIN address_uniq AS a
          ON g.property_id = a.property_id
        WHERE
            (:zip_codes IS NULL OR a.zip_code = ANY(:zip_codes))
            AND (:property_subtype IS NULL OR EXISTS (
                SELECT 1 FROM mls_history m
                WHERE m.property_id = g.property_id
                  AND m.property_use_standardized = :property_subtype
            ))
    )
    SELECT
        zip_code,
        FLOOR(vendor_lot_width_ft / :bucket_size_ft)::int * :bucket_size_ft AS width_bucket,
        FLOOR(vendor_lot_depth_ft / :bucket_size_ft)::int * :bucket_size_ft AS depth_bucket,
        COUNT(*) AS lot_count
    FROM joined
    GROUP BY
        zip_code,
        width_bucket,
        depth_bucket
    ORDER BY
        zip_code,
        width_bucket,
        depth_bucket;
    """

    params = {
        "zip_codes": p.zip_codes,
        "bucket_size_ft": p.bucket_size_ft,
        "property_subtype": p.property_subtype,
        "min_lot_size_sq_ft": p.min_lot_size_sq_ft,
        "max_lot_size_sq_ft": p.max_lot_size_sq_ft,
        "exclude_outliers": p.exclude_outliers,
    }
    rows = [LotSizeBucketRow(**r) for r in _fetch_all(conn, sql, params)]
    return rows


def ranked_zips_ppsf(conn: Connection, p: RankedZipsParams) -> List[RankedZipRow]:
    """
    Query D: Ranked ZIPs by PPSF with 1%-99% trimming and minimum thresholds.
    """
    sql = """
    WITH valid_streets AS MATERIALIZED (
        SELECT
            s.id
        FROM street AS s
        JOIN city AS c
          ON c.id = s.city_id
        WHERE
            UPPER(c.county) = ANY(:allowed_counties)
    ),
    base_sales AS MATERIALIZED (
        SELECT
            a.zip_code,
            (h.sold_price / NULLIF(h.living_sq_ft, 0)) AS ppsf,
            h.living_sq_ft
        FROM mls_history AS h
        JOIN property_address AS a
          ON a.property_id = h.property_id
        WHERE
            h.property_use_standardized = :property_use
            AND h.sold_date >= :min_sold_date
            AND h.sold_price > 0
            AND h.living_sq_ft > 0
            AND a.zip_code IS NOT NULL
            AND (h.sold_price / h.living_sq_ft) BETWEEN :min_ppsf AND :max_ppsf
            AND EXISTS (
                SELECT 1
                FROM valid_streets AS vs
                WHERE vs.id = a.street_id
            )
    ),
    ppsf_bounds AS (
        SELECT
            PERCENTILE_CONT(:trim_lower_pct) WITHIN GROUP (ORDER BY ppsf) AS lower_bound,
            PERCENTILE_CONT(:trim_upper_pct) WITHIN GROUP (ORDER BY ppsf) AS upper_bound
        FROM base_sales
    ),
    zip_stats AS (
        SELECT
            bs.zip_code,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY bs.ppsf) AS median_ppsf,
            AVG(bs.living_sq_ft) AS avg_living_sq_ft,
            COUNT(*) AS sale_count
        FROM base_sales AS bs
        CROSS JOIN ppsf_bounds AS b
        WHERE
            bs.ppsf BETWEEN b.lower_bound AND b.upper_bound
        GROUP BY
            bs.zip_code
    )
    SELECT
        zip_code,
        median_ppsf,
        avg_living_sq_ft,
        sale_count
    FROM zip_stats
    WHERE
        median_ppsf >= :min_median_ppsf
        AND sale_count >= :min_sale_count
    ORDER BY
        median_ppsf DESC;
    """

    params = {
        "allowed_counties": p.allowed_counties,
        "property_use": p.property_use,
        "min_sold_date": p.min_sold_date,
        "min_ppsf": p.min_ppsf,
        "max_ppsf": p.max_ppsf,
        "trim_lower_pct": p.trim_lower_pct,
        "trim_upper_pct": p.trim_upper_pct,
        "min_median_ppsf": p.min_median_ppsf,
        "min_sale_count": p.min_sale_count,
    }
    rows = [RankedZipRow(**r) for r in _fetch_all(conn, sql, params)]
    return rows


# ---- F1 Comps (read-only mode: public tables only) ----

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_F1_COMPS_SQL = _PROJECT_ROOT / "sql" / "readonly" / "f1_comps.sql"
_F3_OFFER_RANGE_SQL = _PROJECT_ROOT / "sql" / "readonly" / "f3_offer_range.sql"
_F4_OVERPAY_RISK_SQL = _PROJECT_ROOT / "sql" / "readonly" / "f4_overpay_risk.sql"
_ZONING_SUMMARY_SQL = _PROJECT_ROOT / "sql" / "readonly" / "zoning_summary.sql"
_PARCEL_CENTER_SQL = _PROJECT_ROOT / "sql" / "readonly" / "parcel_center_point.sql"
_PARCEL_FOOTPRINT_SQL = _PROJECT_ROOT / "sql" / "readonly" / "parcel_footprint.sql"
_PROPERTY_INFO_SQL = _PROJECT_ROOT / "sql" / "readonly" / "property_info.sql"
_NEARBY_ZONING_SQL = _PROJECT_ROOT / "sql" / "readonly" / "nearby_zoning.sql"
_COMPS_AGGREGATE_SQL = _PROJECT_ROOT / "sql" / "readonly" / "comps_aggregate.sql"
_COMPS_AGGREGATE_ROWS_SQL = _PROJECT_ROOT / "sql" / "readonly" / "comps_aggregate_rows.sql"
_VOLUME_BY_ZIP_YEAR_SQL = _PROJECT_ROOT / "sql" / "readonly" / "volume_by_zip_year.sql"
_VOLUME_BY_CITY_YEAR_SQL = _PROJECT_ROOT / "sql" / "readonly" / "volume_by_city_year.sql"
_VOLUME_BY_ZIP_MONTH_SQL = _PROJECT_ROOT / "sql" / "readonly" / "volume_by_zip_month.sql"
_VOLUME_BY_ZIP_MONTH_NO_DOM_SQL = _PROJECT_ROOT / "sql" / "readonly" / "volume_by_zip_month_no_dom.sql"


def f1_comps(conn: Connection, p: F1CompsParams) -> List[F1CompsRow]:
    """
    F1 Comps: read-only mode. Single SELECT from public tables (no analytics schema).
    Tableau and web app can use this when DB has no CREATE rights.
    """
    sql = load_sql(_F1_COMPS_SQL)
    params = {
        "zip_code": p.zip_code.strip(),
        "sale_year": p.sale_year,
        "limit": p.limit,
        "ppsf_min": p.ppsf_min,
        "city_name": _norm_city(p.city_name),
    }
    rows = list(_fetch_all(conn, sql, params))
    return [F1CompsRow(**r) for r in rows]


def f3_offer_range(conn: Connection, p: F3OfferRangeParams) -> List[F3OfferRangeRow]:
    """
    F3 Offer range: read-only. ZIP only; 25th/50th/75th PPSF × living_sq_ft.
    Returns one row or empty if no comps.
    """
    sql = load_sql(_F3_OFFER_RANGE_SQL)
    params = {
        "zip_code": p.zip_code.strip(),
        "sale_year": p.sale_year,
        "living_sq_ft": p.living_sq_ft,
        "ppsf_min": p.ppsf_min,
        "city_name": _norm_city(p.city_name),
    }
    rows = list(_fetch_all(conn, sql, params))
    if not rows or rows[0].get("comp_count", 0) == 0:
        return []
    r = rows[0]
    return [F3OfferRangeRow(
        low_ppsf=float(r["low_ppsf"]) if r.get("low_ppsf") is not None else 0.0,
        base_ppsf=float(r["base_ppsf"]) if r.get("base_ppsf") is not None else 0.0,
        high_ppsf=float(r["high_ppsf"]) if r.get("high_ppsf") is not None else 0.0,
        low_price=float(r["low_price"]) if r.get("low_price") is not None else 0.0,
        base_price=float(r["base_price"]) if r.get("base_price") is not None else 0.0,
        high_price=float(r["high_price"]) if r.get("high_price") is not None else 0.0,
        comp_count=int(r["comp_count"]),
        geography_used=str(r["geography_used"]),
    )]


def f4_overpay_risk(conn: Connection, p: F4OverpayRiskParams) -> List[F4OverpayRiskRow]:
    """
    F4 Overpay risk: read-only. ZIP only; list_price vs comp-based value (median PPSF × living_sq_ft).
    """
    sql = load_sql(_F4_OVERPAY_RISK_SQL)
    params = {
        "zip_code": p.zip_code.strip(),
        "sale_year": p.sale_year,
        "ppsf_min": p.ppsf_min,
        "city_name": _norm_city(p.city_name),
    }
    rows = list(_fetch_all(conn, sql, params))
    if not rows or rows[0].get("comp_count", 0) == 0:
        return []
    r = rows[0]
    median_ppsf = float(r["median_ppsf"])
    comp_based_value = median_ppsf * p.living_sq_ft
    pct_above = ((p.list_price - comp_based_value) / comp_based_value * 100.0) if comp_based_value else 0.0
    if pct_above <= 5.0:
        risk_level = "low"
    elif pct_above <= 12.0:
        risk_level = "medium"
    else:
        risk_level = "high"
    return [F4OverpayRiskRow(
        comp_median_ppsf=median_ppsf,
        comp_based_value=comp_based_value,
        list_price=p.list_price,
        pct_above_comps=round(pct_above, 2),
        risk_level=risk_level,
        comp_count=int(r["comp_count"]),
        geography_used=str(r["geography_used"]),
    )]


def comps_aggregate(conn: Connection, p: CompsAggregateParams) -> List[CompsAggregateRow]:
    """
    Comps aggregate: hard filters (12-month recency, distance cap, size band, property_subtype) + soft weights.
    Returns one row with comp_count, median_ppsf, p25/p75, iqr, median_dom, diagnostics, and confidence_score/band.
    """
    sql = load_sql(_COMPS_AGGREGATE_SQL)
    params = {
        "subject_parcel_id": p.subject_parcel_id,
        "subject_sqft": p.subject_sqft,
        "property_subtype": p.property_subtype,
        "distance_cap_miles": p.distance_cap_miles,
        "size_band_pct": p.size_band_pct,
        "recency_months": p.recency_months,
        "ppsf_min": p.ppsf_min,
        "half_life_months": p.half_life_months,
        "half_life_miles": p.half_life_miles,
        "city_name": _norm_city(p.city_name),
    }
    rows = list(_fetch_all(conn, sql, params))
    if not rows:
        return [CompsAggregateRow(comp_count=0, confidence_band="low")]
    r = rows[0]
    comp_count = int(r.get("comp_count") or 0)
    median_ppsf = float(r["median_ppsf"]) if r.get("median_ppsf") is not None else None
    iqr_ppsf = float(r["iqr_ppsf"]) if r.get("iqr_ppsf") is not None else None
    median_dist_miles = float(r["median_dist_miles"]) if r.get("median_dist_miles") is not None else None
    median_months_ago = float(r["median_months_ago"]) if r.get("median_months_ago") is not None else None

    confidence_score_val = None
    confidence_band_val = None
    coverage_val = None
    proximity_val = None
    recency_val = None
    tightness_val = None
    hint_val = None
    if comp_count > 0:
        confidence_score_val, confidence_band_val = confidence_score_and_band(
            comp_count=comp_count,
            median_ppsf=median_ppsf,
            iqr_ppsf=iqr_ppsf,
            median_dist_miles=median_dist_miles,
            median_months_ago=median_months_ago,
            recency_halflife_months=p.half_life_months,
            proximity_halflife_miles=p.half_life_miles,
        )
        coverage_val, proximity_val, recency_val, tightness_val = confidence_components(
            comp_count=comp_count,
            median_ppsf=median_ppsf,
            iqr_ppsf=iqr_ppsf,
            median_dist_miles=median_dist_miles,
            median_months_ago=median_months_ago,
            recency_halflife_months=p.half_life_months,
            proximity_halflife_miles=p.half_life_miles,
        )
    else:
        # When 0 comps, check if subject has no location (common cause).
        sub_geom = list(_fetch_all(conn, "SELECT 1 FROM property_geometry WHERE property_id = :id AND center_point IS NOT NULL AND ST_IsValid(center_point::geometry) LIMIT 1", {"id": p.subject_parcel_id}))
        if not sub_geom:
            hint_val = "Subject property has no location in property_geometry (or center_point is null/invalid). Add geometry to find nearby comps."

    pct_20 = float(r["pct_within_20pct_sqft"]) if r.get("pct_within_20pct_sqft") is not None else None
    spread_ratio_val = (iqr_ppsf / median_ppsf) if (median_ppsf and median_ppsf > 0 and iqr_ppsf is not None) else None
    p75_val = float(r["p75_ppsf"]) if r.get("p75_ppsf") is not None else None
    upside_score_val = ((p75_val - median_ppsf) / median_ppsf) if (median_ppsf and median_ppsf > 0 and p75_val is not None) else None

    return [CompsAggregateRow(
        comp_count=comp_count,
        median_ppsf=median_ppsf,
        p25_ppsf=float(r["p25_ppsf"]) if r.get("p25_ppsf") is not None else None,
        p75_ppsf=p75_val,
        iqr_ppsf=iqr_ppsf,
        median_dom=float(r["median_dom"]) if r.get("median_dom") is not None else None,
        p75_dom=float(r["p75_dom"]) if r.get("p75_dom") is not None else None,
        median_dist_miles=median_dist_miles,
        median_months_ago=median_months_ago,
        pct_within_025mi=float(r["pct_within_025mi"]) if r.get("pct_within_025mi") is not None else None,
        pct_within_05mi=float(r["pct_within_05mi"]) if r.get("pct_within_05mi") is not None else None,
        pct_within_3mo=float(r["pct_within_3mo"]) if r.get("pct_within_3mo") is not None else None,
        pct_within_6mo=float(r["pct_within_6mo"]) if r.get("pct_within_6mo") is not None else None,
        pct_within_20pct_sqft=pct_20,
        match_rate=pct_20,
        ppsf_spread=iqr_ppsf,
        spread_ratio=round(spread_ratio_val, 4) if spread_ratio_val is not None else None,
        expected_ppsf=median_ppsf,
        upside_score=round(upside_score_val, 4) if upside_score_val is not None else None,
        confidence_score=confidence_score_val,
        confidence_band=confidence_band_val,
        confidence_coverage=coverage_val,
        confidence_proximity=proximity_val,
        confidence_recency=recency_val,
        confidence_tightness=tightness_val,
        hint=hint_val,
    )]


def comps_aggregate_rows(conn: Connection, p: CompsAggregateParams, limit: int = 50) -> List[CompsAggregateCompRow]:
    """
    Row-level comps with weights (same filters as comps_aggregate). Returns list of comp rows with dist_miles, months_ago, w.
    """
    sql = load_sql(_COMPS_AGGREGATE_ROWS_SQL)
    params = {
        "subject_parcel_id": p.subject_parcel_id,
        "subject_sqft": p.subject_sqft,
        "property_subtype": p.property_subtype,
        "distance_cap_miles": p.distance_cap_miles,
        "size_band_pct": p.size_band_pct,
        "recency_months": p.recency_months,
        "ppsf_min": p.ppsf_min,
        "half_life_months": p.half_life_months,
        "half_life_miles": p.half_life_miles,
        "city_name": _norm_city(p.city_name),
        "limit": min(limit, 100),
    }
    rows = list(_fetch_all(conn, sql, params))
    return [CompsAggregateCompRow(**r) for r in rows]


def _opt_str(v: Optional[str]) -> Optional[str]:
    """None or empty string -> None; otherwise stripped."""
    if v is None:
        return None
    s = (v if isinstance(v, str) else str(v)).strip()
    return s if s else None


def _norm_city(city_name: Optional[str]) -> str:
    """Normalize city for SQL: uppercase, trim; default LOS ANGELES."""
    s = _opt_str(city_name)
    return (s.upper() if s else "LOS ANGELES")


def volume_by_zip_year(conn: Connection, p: VolumeByZipYearParams) -> List[VolumeByZipYearRow]:
    """Volume and liquidity by ZIP × year for web viz (bar, line)."""
    sql = load_sql(_VOLUME_BY_ZIP_YEAR_SQL)
    params = {"min_sold_date": p.min_sold_date, "zip_code": _opt_str(p.zip_code), "city_name": _norm_city(p.city_name)}
    rows = list(_fetch_all(conn, sql, params))
    return [VolumeByZipYearRow(**r) for r in rows]


def volume_by_city_year(conn: Connection, p: VolumeByCityYearParams) -> List[VolumeByCityYearRow]:
    """Volume by city × year for web viz (line charts)."""
    sql = load_sql(_VOLUME_BY_CITY_YEAR_SQL)
    params = {"min_sold_date": p.min_sold_date, "city_name": _norm_city(p.city_name)}
    rows = list(_fetch_all(conn, sql, params))
    return [VolumeByCityYearRow(**r) for r in rows]


def volume_by_zip_month(conn: Connection, p: VolumeByZipMonthParams) -> List[VolumeByZipMonthRow]:
    """Volume by ZIP × month for web viz (seasonality line, heatmap). Tries with days_on_market first; falls back to no-dom if column missing."""
    params = {"min_sold_date": p.min_sold_date, "zip_code": _opt_str(p.zip_code), "city_name": _norm_city(p.city_name)}
    for path in (_VOLUME_BY_ZIP_MONTH_SQL, _VOLUME_BY_ZIP_MONTH_NO_DOM_SQL):
        try:
            sql = load_sql(path)
            rows = list(_fetch_all(conn, sql, params))
            return [VolumeByZipMonthRow(**r) for r in rows]
        except Exception:
            continue
    raise RuntimeError("volume_by_zip_month failed with both SQL variants")


# ---- Week 3: Zoning summary ("what you can build") ----
# Zone-code lookup (aligns with src/feasibility/zoning_constraints.DEFAULT_LA_ZONE_LOOKUP).
_ZONE_LOOKUP = {
    "R1": {"max_far": 0.5, "max_height_ft": 30.0, "min_parking_spaces": 2.0, "max_units": 1},
    "R2": {"max_far": 0.5, "max_height_ft": 30.0, "min_parking_spaces": 2.0, "max_units": 2},
    "RS": {"max_far": 0.5, "max_height_ft": 30.0, "min_parking_spaces": 2.0, "max_units": 1},
    "RE": {"max_far": 0.35, "max_height_ft": 28.0, "min_parking_spaces": 2.0, "max_units": 1},
    "RM": {"max_far": 1.25, "max_height_ft": 45.0, "min_parking_spaces": 1.5, "max_units": 8},
}


def zoning_summary(conn: Connection, p: ZoningSummaryParams) -> List[ZoningSummaryRow]:
    """
    Zoning summary for one parcel: zone_code, lot_size_sq_ft, and constraint estimates from zone lookup.
    Read-only; uses public tables (parcel_gold join path: property_address, property_zoning, zone, property_geometry).
    """
    sql = load_sql(_ZONING_SUMMARY_SQL)
    rows = list(_fetch_all(conn, sql, {"parcel_id": p.parcel_id}))
    if not rows:
        return []
    r = rows[0]
    parcel_id = int(r["parcel_id"])
    zone_code = str(r["zone_code"]).strip() if r.get("zone_code") else None
    lot_sq_ft = float(r["lot_size_sq_ft"]) if r.get("lot_size_sq_ft") is not None else None

    max_gfa = None
    max_height_ft = None
    min_parking_spaces = None
    max_units = None
    if zone_code and zone_code in _ZONE_LOOKUP:
        lu = _ZONE_LOOKUP[zone_code]
        max_far = lu["max_far"]
        max_height_ft = lu["max_height_ft"]
        min_parking_spaces = lu["min_parking_spaces"]
        max_units = lu["max_units"]
        if lot_sq_ft is not None:
            max_gfa = round(lot_sq_ft * max_far, 2)

    return [ZoningSummaryRow(
        parcel_id=parcel_id,
        zone_code=zone_code,
        lot_size_sq_ft=lot_sq_ft,
        max_gfa_estimate=max_gfa,
        max_height_ft=max_height_ft,
        min_parking_spaces=min_parking_spaces,
        max_units=max_units,
    )]


def parcel_center(conn: Connection, p: ParcelCenterParams) -> List[ParcelCenterRow]:
    """
    Center point (lon, lat) for one parcel. For proximity-to-essentials: use with external POI.
    """
    sql = load_sql(_PARCEL_CENTER_SQL)
    rows = list(_fetch_all(conn, sql, {"parcel_id": p.parcel_id}))
    if not rows:
        return []
    r = rows[0]
    return [ParcelCenterRow(
        parcel_id=int(r["parcel_id"]),
        longitude=float(r["longitude"]),
        latitude=float(r["latitude"]),
    )]


def _footprint_ratio_band(aspect_ratio: float) -> str:
    """Orientation-free aspect_ratio (>=1): balanced (1.0–1.3), moderate (1.3–2.0), extreme (>2.0)."""
    if aspect_ratio <= 1.3:
        return "balanced"
    if aspect_ratio <= 2.0:
        return "moderate"
    return "extreme"


def parcel_footprint(conn: Connection, p: ParcelFootprintParams) -> List[ParcelFootprintRow]:
    """
    Lot footprint for one parcel: width, depth, aspect_ratio, ratio_band; data quality fields.
    Width = frontage (vendor_lot_width_ft), depth = lot depth (vendor_lot_depth_ft).
    Returns one row even when invalid (is_valid_dimensions=False, notes set).
    """
    sql = load_sql(_PARCEL_FOOTPRINT_SQL)
    rows = list(_fetch_all(conn, sql, {"property_id": p.property_id}))
    if not rows:
        return [ParcelFootprintRow(
            property_id=p.property_id,
            lot_size_sq_ft=None,
            lot_width_ft=None,
            lot_depth_ft=None,
            width_to_depth_ratio=None,
            aspect_ratio=None,
            ratio_band="",
            width_source=None,
            depth_source=None,
            is_valid_dimensions=False,
            notes="No geometry row for this property_id.",
        )]
    r = rows[0]
    pid = int(r["property_id"])
    lot_sqft = float(r["lot_size_sq_ft"]) if r.get("lot_size_sq_ft") is not None else None
    v_w = r.get("vendor_lot_width_ft")
    v_d = r.get("vendor_lot_depth_ft")
    i_w = r.get("inferred_lot_width_ft") if "inferred_lot_width_ft" in r else None
    i_d = r.get("inferred_lot_depth_ft") if "inferred_lot_depth_ft" in r else None
    w_val = float(v_w) if v_w is not None and float(v_w) > 0 else (float(i_w) if i_w is not None and float(i_w) > 0 else None)
    d_val = float(v_d) if v_d is not None and float(v_d) > 0 else (float(i_d) if i_d is not None and float(i_d) > 0 else None)
    width_src = "vendor" if v_w is not None and float(v_w) > 0 else ("inferred" if w_val is not None else None)
    depth_src = "vendor" if v_d is not None and float(v_d) > 0 else ("inferred" if d_val is not None else None)
    notes_list = []
    if w_val is None:
        notes_list.append("width missing or zero")
    if d_val is None:
        notes_list.append("depth missing or zero")
    notes_str = "; ".join(notes_list) if notes_list else None
    if w_val is None or d_val is None:
        return [ParcelFootprintRow(
            property_id=pid,
            lot_size_sq_ft=lot_sqft,
            lot_width_ft=w_val,
            lot_depth_ft=d_val,
            width_to_depth_ratio=None,
            aspect_ratio=None,
            ratio_band="",
            width_source=width_src,
            depth_source=depth_src,
            is_valid_dimensions=False,
            notes=notes_str,
        )]
    w, d = w_val, d_val
    lo, hi = min(w, d), max(w, d)
    aspect = round((hi / lo), 3) if lo and lo > 0 else None
    width_to_depth = round((w / d), 3) if d and d > 0 else None
    return [ParcelFootprintRow(
        property_id=pid,
        lot_size_sq_ft=lot_sqft,
        lot_width_ft=round(w, 2),
        lot_depth_ft=round(d, 2),
        width_to_depth_ratio=width_to_depth,
        aspect_ratio=aspect,
        ratio_band=_footprint_ratio_band(hi / lo),
        width_source=width_src,
        depth_source=depth_src,
        is_valid_dimensions=True,
        notes=notes_str,
    )]


def property_info(conn: Connection, p: PropertyInfoParams) -> List[PropertyInfoRow]:
    """
    Latest mls_history row for one property_id: sold_date, sold_price, living_sq_ft, zip, city, etc.
    Returns at most one row; empty if property has no valid sale in mls_history.
    """
    sql = load_sql(_PROPERTY_INFO_SQL)
    rows = list(_fetch_all(conn, sql, {"property_id": p.property_id}))
    if not rows:
        return []
    r = rows[0]
    return [PropertyInfoRow(
        sale_id=int(r["sale_id"]),
        property_id=int(r["property_id"]),
        sold_date=r["sold_date"],
        sold_price=float(r["sold_price"]),
        living_sq_ft=float(r["living_sq_ft"]),
        ppsf=float(r["ppsf"]),
        days_on_market=float(r["days_on_market"]) if r.get("days_on_market") is not None else None,
        year_built=int(r["year_built"]) if r.get("year_built") is not None else None,
        property_use_standardized=str(r["property_use_standardized"]) if r.get("property_use_standardized") else None,
        zip_code=str(r["zip_code"]) if r.get("zip_code") else None,
        city_name=str(r["city_name"]) if r.get("city_name") else None,
    )]


def nearby_zoning(conn: Connection, p: NearbyZoningParams) -> List[NearbyZoningRow]:
    """
    Week 3: Zoning for subject parcel + nearby parcels (same ZIP). From property_zoning + zone.
    """
    sql = load_sql(_NEARBY_ZONING_SQL)
    params = {"parcel_id": p.parcel_id, "limit": p.limit}
    rows = list(_fetch_all(conn, sql, params))
    return [
        NearbyZoningRow(
            parcel_id=int(r["parcel_id"]),
            zip_code=str(r["zip_code"]) if r.get("zip_code") else None,
            zone_code=str(r["zone_code"]) if r.get("zone_code") else None,
            is_subject=bool(r.get("is_subject")),
        )
        for r in rows
    ]


# ---- Week 2: Comps, PPSF map, offer range, overpay risk ----

def comps(conn: Connection, p: CompsParams) -> List[CompsRow]:
    """
    Comparable sales: by zip or by lat/lon (resolves to 0.25-mi cell).
    Uses analytics.mv_sale_la_since2020_ppsf400 (LA, 2020+, ppsf>=400).
    """
    if p.latitude is not None and p.longitude is not None:
        sql = """
        WITH cell_lookup AS (
            SELECT g.cell_id
            FROM analytics.grid_cells_025 g
            WHERE ST_Intersects(
                ST_Transform(ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326), 3310),
                g.geom_3310
            )
            LIMIT 1
        ),
        cell_sales AS (
            SELECT s.sale_id, s.property_id, s.sold_date, s.sold_price, s.living_sq_ft,
                   s.ppsf, s.zip_code, s.city_name, s.year_built
            FROM analytics.mv_sale_la_since2020_ppsf400 s
            JOIN analytics.grid_cells_025 g
              ON s.point_3310 IS NOT NULL AND ST_Intersects(s.point_3310, g.geom_3310)
            JOIN cell_lookup c ON g.cell_id = c.cell_id
            WHERE s.sale_year = :sale_year
        )
        SELECT * FROM cell_sales
        ORDER BY sold_date DESC
        LIMIT :limit
        """
        params = {
            "latitude": p.latitude,
            "longitude": p.longitude,
            "sale_year": p.sale_year,
            "limit": p.limit,
        }
    elif p.zip_code:
        sql = """
        SELECT sale_id, property_id, sold_date, sold_price, living_sq_ft,
               ppsf, zip_code, city_name, year_built
        FROM analytics.mv_sale_la_since2020_ppsf400
        WHERE zip_code = :zip_code AND sale_year = :sale_year
        ORDER BY sold_date DESC
        LIMIT :limit
        """
        params = {"zip_code": p.zip_code.strip(), "sale_year": p.sale_year, "limit": p.limit}
    else:
        return []
    return [CompsRow(**r) for r in _fetch_all(conn, sql, params)]


def ppsf_map(conn: Connection, p: PpsfMapParams) -> List[PpsfMapRow]:
    """
    PPSF map: grid (0.25-mi) or zip level with median_ppsf, comp_count, confidence_band.
    """
    if p.geography == "zip":
        sql = """
        SELECT
            zip_code AS geo_id,
            NULL::float AS centroid_lon,
            NULL::float AS centroid_lat,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
            AVG(ppsf) AS avg_ppsf,
            COUNT(*)::int AS comp_count,
            CASE
                WHEN COUNT(*) < 20 THEN 'low'
                WHEN COUNT(*) < 50 THEN 'med'
                ELSE 'high'
            END AS confidence_band
        FROM analytics.mv_sale_la_since2020_ppsf400
        WHERE sale_year = :sale_year AND zip_code IS NOT NULL
        GROUP BY zip_code
        ORDER BY comp_count DESC
        LIMIT :limit
        """
        params = {"sale_year": p.sale_year, "limit": p.limit}
    else:
        sql = """
        SELECT
            agg.cell_id::text AS geo_id,
            g.centroid_lon,
            g.centroid_lat,
            agg.median_ppsf,
            agg.avg_ppsf,
            agg.comp_count,
            agg.confidence_band
        FROM analytics.mv_agg_grid_year_ppsf_025 agg
        JOIN analytics.grid_cells_025 g ON g.cell_id = agg.cell_id
        WHERE agg.sale_year = :sale_year
        ORDER BY agg.comp_count DESC
        LIMIT :limit
        """
        params = {"sale_year": p.sale_year, "limit": p.limit}
    return [PpsfMapRow(**r) for r in _fetch_all(conn, sql, params)]


def offer_range(conn: Connection, p: OfferRangeParams) -> List[OfferRangeRow]:
    """
    Recommended offer range: 25th/50th/75th percentile PPSF for geography × year, then × living_sq_ft.
    """
    if p.cell_id is not None:
        sql = """
        WITH cell_sales AS (
            SELECT s.ppsf
            FROM analytics.mv_sale_la_since2020_ppsf400 s
            JOIN analytics.grid_cells_025 g
              ON s.point_3310 IS NOT NULL AND ST_Intersects(s.point_3310, g.geom_3310)
            WHERE g.cell_id = :cell_id AND s.sale_year = :sale_year
        ),
        pct AS (
            SELECT
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ppsf) AS p25,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS p50,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ppsf) AS p75,
                COUNT(*)::int AS comp_count
            FROM cell_sales
        )
        SELECT
            p25 AS low_ppsf, p50 AS base_ppsf, p75 AS high_ppsf,
            p25 * :living_sq_ft AS low_price,
            p50 * :living_sq_ft AS base_price,
            p75 * :living_sq_ft AS high_price,
            comp_count,
            'cell_025' AS geography_used
        FROM pct
        """
        params = {"cell_id": str(p.cell_id), "sale_year": p.sale_year, "living_sq_ft": p.living_sq_ft}
    elif p.zip_code:
        sql = """
        WITH zip_sales AS (
            SELECT ppsf FROM analytics.mv_sale_la_since2020_ppsf400
            WHERE zip_code = :zip_code AND sale_year = :sale_year
        ),
        pct AS (
            SELECT
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ppsf) AS p25,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS p50,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ppsf) AS p75,
                COUNT(*)::int AS comp_count
            FROM zip_sales
        )
        SELECT
            p25 AS low_ppsf, p50 AS base_ppsf, p75 AS high_ppsf,
            p25 * :living_sq_ft AS low_price,
            p50 * :living_sq_ft AS base_price,
            p75 * :living_sq_ft AS high_price,
            comp_count,
            'zip' AS geography_used
        FROM pct
        """
        params = {"zip_code": p.zip_code.strip(), "sale_year": p.sale_year, "living_sq_ft": p.living_sq_ft}
    else:
        return []
    rows = list(_fetch_all(conn, sql, params))
    if not rows or rows[0].get("comp_count", 0) == 0:
        return []
    r = rows[0]
    return [OfferRangeRow(
        low_ppsf=float(r["low_ppsf"]) if r.get("low_ppsf") is not None else 0.0,
        base_ppsf=float(r["base_ppsf"]) if r.get("base_ppsf") is not None else 0.0,
        high_ppsf=float(r["high_ppsf"]) if r.get("high_ppsf") is not None else 0.0,
        low_price=float(r["low_price"]) if r.get("low_price") is not None else 0.0,
        base_price=float(r["base_price"]) if r.get("base_price") is not None else 0.0,
        high_price=float(r["high_price"]) if r.get("high_price") is not None else 0.0,
        comp_count=int(r["comp_count"]),
        geography_used=str(r["geography_used"]),
    )]


def overpay_risk(conn: Connection, p: OverpayRiskParams) -> List[OverpayRiskRow]:
    """
    Overpay risk: comp-based value (median PPSF × living_sq_ft) vs list price; pct above and risk level.
    """
    if p.cell_id is not None:
        sql = """
        SELECT
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.ppsf) AS median_ppsf,
            COUNT(*)::int AS comp_count,
            'cell_025' AS geography_used
        FROM analytics.mv_sale_la_since2020_ppsf400 s
        JOIN analytics.grid_cells_025 g
          ON s.point_3310 IS NOT NULL AND ST_Intersects(s.point_3310, g.geom_3310)
        WHERE g.cell_id = :cell_id AND s.sale_year = :sale_year
        """
        params = {"cell_id": str(p.cell_id), "sale_year": p.sale_year}
    elif p.zip_code:
        sql = """
        SELECT
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
            COUNT(*)::int AS comp_count,
            'zip' AS geography_used
        FROM analytics.mv_sale_la_since2020_ppsf400
        WHERE zip_code = :zip_code AND sale_year = :sale_year
        """
        params = {"zip_code": p.zip_code.strip(), "sale_year": p.sale_year}
    else:
        return []
    rows = list(_fetch_all(conn, sql, params))
    if not rows or rows[0].get("comp_count", 0) == 0:
        return []
    r = rows[0]
    median_ppsf = float(r["median_ppsf"])
    comp_based_value = median_ppsf * p.living_sq_ft
    pct_above = ((p.list_price - comp_based_value) / comp_based_value * 100.0) if comp_based_value else 0.0
    if pct_above <= 5.0:
        risk_level = "low"
    elif pct_above <= 12.0:
        risk_level = "medium"
    else:
        risk_level = "high"
    return [OverpayRiskRow(
        comp_median_ppsf=median_ppsf,
        comp_based_value=comp_based_value,
        list_price=p.list_price,
        pct_above_comps=round(pct_above, 2),
        risk_level=risk_level,
        comp_count=int(r["comp_count"]),
        geography_used=str(r["geography_used"]),
    )]


def confidence_coverage(conn: Connection, p: ConfidenceCoverageParams) -> List[ConfidenceCoverageRow]:
    """
    Confidence and coverage: comp_count, confidence_band, effective tier, human-readable message.
    """
    if p.cell_id is not None:
        sql = """
        SELECT
            t.cell_id::text AS geo_id,
            t.comp_025 AS comp_count,
            CASE
                WHEN t.comp_025 >= 20 THEN t.comp_025
                WHEN t.comp_3x3 >= 20 THEN t.comp_3x3
                WHEN t.comp_5x5 >= 20 THEN t.comp_5x5
                WHEN t.comp_zip >= 20 THEN t.comp_zip
                ELSE t.comp_city
            END AS effective_comp_count,
            t.effective_tier,
            t.effective_geometry_type,
            CASE
                WHEN t.comp_025 >= 20 THEN 'high'
                WHEN t.comp_025 >= 10 THEN 'med'
                ELSE 'low'
            END AS confidence_band
        FROM analytics.v_grid_year_effective_tier t
        WHERE t.cell_id = :cell_id AND t.sale_year = :sale_year
        """
        params = {"cell_id": str(p.cell_id), "sale_year": p.sale_year}
        rows = list(_fetch_all(conn, sql, params))
        if not rows:
            return []
        r = rows[0]
        geo_used = "cell_025"
        comp_count = int(r.get("comp_count", 0))
        band = str(r.get("confidence_band", "low"))
        tier = int(r["effective_tier"]) if r.get("effective_tier") is not None else None
        geom_type = str(r["effective_geometry_type"]) if r.get("effective_geometry_type") else None
        if comp_count < 20 and tier and tier > 1:
            msg = f"Low sample in 0.25-mi cell ({comp_count} comps). Estimate uses {geom_type or 'wider area'} (tier {tier}) with ≥20 comps."
        elif comp_count < 10:
            msg = f"Low confidence: only {comp_count} comparable sales in this area. Consider widening search."
        else:
            msg = f"Based on {comp_count} comparable sales in this cell. Confidence: {band}."
        return [ConfidenceCoverageRow(
            geography_used=geo_used,
            geo_id=str(r["geo_id"]),
            comp_count=comp_count,
            confidence_band=band,
            effective_tier=tier,
            effective_geometry_type=geom_type,
            message=msg,
        )]
    elif p.zip_code:
        sql = """
        SELECT comp_zip AS comp_count
        FROM analytics.v_zip_year_comp
        WHERE zip_code = :zip_code AND sale_year = :sale_year
        """
        params = {"zip_code": p.zip_code.strip(), "sale_year": p.sale_year}
        rows = list(_fetch_all(conn, sql, params))
        if not rows:
            return []
        comp_count = int(rows[0].get("comp_count", 0))
        if comp_count < 20:
            band = "low"
            msg = f"ZIP has {comp_count} comps; below 20. Consider city-level or wider geography for higher confidence."
        elif comp_count < 50:
            band = "med"
            msg = f"Based on {comp_count} comps in this ZIP. Confidence: medium."
        else:
            band = "high"
            msg = f"Based on {comp_count} comps in this ZIP. Confidence: high."
        return [ConfidenceCoverageRow(
            geography_used="zip",
            geo_id=p.zip_code.strip(),
            comp_count=comp_count,
            confidence_band=band,
            effective_tier=4,
            effective_geometry_type="zip",
            message=msg,
        )]
    return []

