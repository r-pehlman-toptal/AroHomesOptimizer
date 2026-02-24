from __future__ import annotations

from typing import Any, Dict, Iterable, List

from sqlalchemy import text
from sqlalchemy.engine import Connection

from src.query_service.schemas import (
    BedBathDistributionParams,
    BedBathDistributionRow,
    PrincipalZoneParams,
    PrincipalZoneRow,
    LotSizeBucketsParams,
    LotSizeBucketRow,
    RankedZipsParams,
    RankedZipRow,
)


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
            pg.vendor_lot_depth_ft
        FROM property_geometry AS pg
        WHERE
            pg.vendor_lot_width_ft IS NOT NULL
            AND pg.vendor_lot_depth_ft IS NOT NULL
            AND pg.vendor_lot_width_ft > 0
            AND pg.vendor_lot_depth_ft > 0
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

