from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple
import json

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sklearn.linear_model import LinearRegression

from src.analytics.schemas import (
    LotHeatmapJobParams,
    RegressionJobParams,
    ScenarioJobParams,
    ValueMapJobParams,
)


def _run_query(conn: Connection, sql: str, params: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    result = conn.execute(text(sql), params)
    for row in result.mappings():
        yield dict(row)


def run_lot_heatmap_job(conn: Connection, p: LotHeatmapJobParams) -> None:
    """
    Compute lot size heatmap buckets and persist to analytics_lot_heatmap.
    """
    # Clear previous rows for this scope/market to keep results idempotent for given params.
    conn.execute(
        text(
            """
            DELETE FROM analytics_lot_heatmap
            WHERE scope = :scope AND COALESCE(market_name, '') = COALESCE(:market_name, '');
            """
        ),
        {"scope": p.scope.scope, "market_name": p.scope.market_name},
    )

    sql = """
    WITH address_uniq AS (
        SELECT
            pa.property_id,
            MIN(pa.zip_code) AS zip_code
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
    ),
    joined AS (
        SELECT
            a.zip_code,
            g.vendor_lot_width_ft,
            g.vendor_lot_depth_ft,
            g.lot_size_sq_ft
        FROM geom AS g
        JOIN address_uniq AS a
          ON g.property_id = a.property_id
        WHERE a.zip_code IS NOT NULL
    )
    SELECT
        zip_code,
        CASE
            WHEN :bucket_mode = 'width_depth'
                 AND vendor_lot_width_ft IS NOT NULL AND vendor_lot_width_ft > 0
            THEN FLOOR(vendor_lot_width_ft / :width_bucket_ft)::int * :width_bucket_ft
            ELSE NULL
        END AS width_bucket_ft,
        CASE
            WHEN :bucket_mode = 'width_depth'
                 AND vendor_lot_depth_ft IS NOT NULL AND vendor_lot_depth_ft > 0
            THEN FLOOR(vendor_lot_depth_ft / :depth_bucket_ft)::int * :depth_bucket_ft
            ELSE NULL
        END AS depth_bucket_ft,
        CASE
            WHEN :bucket_mode = 'lot_size'
                 AND lot_size_sq_ft IS NOT NULL AND lot_size_sq_ft > 0
            THEN FLOOR(lot_size_sq_ft / :lot_size_bucket_sqft)::int * :lot_size_bucket_sqft
            ELSE NULL
        END AS lot_size_bucket_sqft,
        COUNT(*) FILTER (
            WHERE
                (:bucket_mode = 'width_depth'
                    AND vendor_lot_width_ft IS NOT NULL AND vendor_lot_width_ft > 0
                    AND vendor_lot_depth_ft IS NOT NULL AND vendor_lot_depth_ft > 0)
             OR (:bucket_mode = 'lot_size'
                    AND lot_size_sq_ft IS NOT NULL AND lot_size_sq_ft > 0)
        ) AS lot_count,
        COUNT(*) FILTER (
            WHERE
                :bucket_mode = 'width_depth'
                AND (vendor_lot_width_ft IS NULL OR vendor_lot_width_ft <= 0
                     OR vendor_lot_depth_ft IS NULL OR vendor_lot_depth_ft <= 0)
        ) AS missing_geom_count
    FROM joined
    GROUP BY
        zip_code,
        width_bucket_ft,
        depth_bucket_ft,
        lot_size_bucket_sqft;
    """

    params = {
        "bucket_mode": p.bucket_mode,
        "width_bucket_ft": p.width_bucket_ft,
        "depth_bucket_ft": p.depth_bucket_ft,
        "lot_size_bucket_sqft": p.lot_size_bucket_sqft,
    }

    rows = list(_run_query(conn, sql, params))
    for r in rows:
        conn.execute(
            text(
                """
                INSERT INTO analytics_lot_heatmap (
                    scope,
                    market_name,
                    geo_unit_type,
                    geo_unit_value,
                    width_bucket_ft,
                    depth_bucket_ft,
                    lot_size_bucket_sqft,
                    lot_count,
                    missing_geom_count,
                    params
                )
                VALUES (
                    :scope,
                    :market_name,
                    :geo_unit_type,
                    :geo_unit_value,
                    :width_bucket_ft,
                    :depth_bucket_ft,
                    :lot_size_bucket_sqft,
                    :lot_count,
                    :missing_geom_count,
                    :params::jsonb
                );
                """
            ),
            {
                "scope": p.scope.scope,
                "market_name": p.scope.market_name,
                "geo_unit_type": p.geo_unit_type,
                "geo_unit_value": r["zip_code"],
                "width_bucket_ft": r["width_bucket_ft"],
                "depth_bucket_ft": r["depth_bucket_ft"],
                "lot_size_bucket_sqft": r["lot_size_bucket_sqft"],
                "lot_count": r["lot_count"],
                "missing_geom_count": r["missing_geom_count"],
                "params": json.dumps(p.to_params_json()),
            },
        )


def _load_regression_dataframe(conn: Connection, p: RegressionJobParams) -> pd.DataFrame:
    date_end = p.date_range_end or pd.Timestamp.today().date()

    sql = """
    SELECT
        h.property_id,
        h.sold_price,
        h.living_sq_ft,
        h.sold_date
    FROM mls_history AS h
    WHERE
        h.property_use_standardized = :property_use
        AND h.sold_date >= :date_start
        AND h.sold_date <= :date_end
        AND h.sold_price > 0
        AND h.living_sq_ft > 0
        AND h.sold_date IS NOT NULL;
    """

    df = pd.read_sql_query(
        sql,
        conn,
        params={
            "property_use": p.property_use,
            "date_start": p.date_range_start,
            "date_end": date_end,
        },
    )
    # Simple features: delta_sqft vs price_per_sqft, trimmed to [min_ppsf, max_ppsf].
    df["price_per_sqft"] = df["sold_price"] / df["living_sq_ft"]
    df = df[(df["price_per_sqft"] >= p.min_ppsf) & (df["price_per_sqft"] <= p.max_ppsf)]
    return df


def run_regression_job(conn: Connection, p: RegressionJobParams) -> int:
    """
    Fit a simple linear regression for value added per sqft and persist summary.

    Returns:
        regression_run_id
    """
    df = _load_regression_dataframe(conn, p)
    if df.empty:
        raise ValueError("No data available for regression with given parameters.")

    # For MVP: regress sold_price on living_sq_ft.
    X = df[["living_sq_ft"]].values.astype(float)
    y = df["sold_price"].values.astype(float)

    model = LinearRegression()
    model.fit(X, y)
    coef_sqft = float(model.coef_[0])
    intercept = float(model.intercept_)

    # Compute simple R^2.
    y_pred = model.predict(X)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    params_json = p.to_params_json()

    res = conn.execute(
        text(
            """
            INSERT INTO analytics_regression_runs (
                scope,
                market_name,
                geo_filter,
                property_filters,
                date_range_start,
                date_range_end,
                coef_sqft,
                intercept,
                r_squared,
                sample_size,
                params
            )
            VALUES (
                :scope,
                :market_name,
                :geo_filter::jsonb,
                :property_filters::jsonb,
                :date_start,
                :date_end,
                :coef_sqft,
                :intercept,
                :r_squared,
                :sample_size,
                :params::jsonb
            )
            RETURNING id;
            """
        ),
        {
            "scope": p.scope.scope,
            "market_name": p.scope.market_name,
            "geo_filter": None,
            "property_filters": None,
            "date_start": p.date_range_start,
            "date_end": p.date_range_end or pd.Timestamp.today().date(),
            "coef_sqft": coef_sqft,
            "intercept": intercept,
            "r_squared": r_squared,
            "sample_size": len(df),
            "params": json.dumps(params_json),
        },
    )
    regression_run_id = res.scalar_one()
    return int(regression_run_id)


def _get_regression_coeffs(conn: Connection, regression_run_id: int) -> Tuple[float, float]:
    res = conn.execute(
        text(
            """
            SELECT coef_sqft, intercept
            FROM analytics_regression_runs
            WHERE id = :id;
            """
        ),
        {"id": regression_run_id},
    )
    row = res.one()
    return float(row[0]), float(row[1])


def run_home_size_scenarios(conn: Connection, p: ScenarioJobParams) -> None:
    """
    Use a stored regression run to evaluate candidate home sizes.
    """
    coef_sqft, intercept = _get_regression_coeffs(conn, p.regression_run_id)

    # Fetch regression scope/market for denormalization.
    res = conn.execute(
        text(
            """
            SELECT scope, market_name
            FROM analytics_regression_runs
            WHERE id = :id;
            """
        ),
        {"id": p.regression_run_id},
    )
    scope, market_name = res.one()

    # Clear previous scenarios for this run to keep it idempotent.
    conn.execute(
        text(
            """
            DELETE FROM analytics_home_size_scenarios
            WHERE regression_run_id = :id;
            """
        ),
        {"id": p.regression_run_id},
    )

    sizes = list(range(p.size_min, p.size_max + 1, p.size_step))
    for size in sizes:
        predicted_value = intercept + coef_sqft * size
        non_zero_count = 1 if predicted_value > 0 else 0
        total_value = predicted_value if predicted_value > 0 else 0.0
        avg_non_zero_value = predicted_value if predicted_value > 0 else 0.0

        conn.execute(
            text(
                """
                INSERT INTO analytics_home_size_scenarios (
                    regression_run_id,
                    scope,
                    market_name,
                    size_sqft,
                    non_zero_count,
                    total_value,
                    avg_non_zero_value,
                    config
                )
                VALUES (
                    :regression_run_id,
                    :scope,
                    :market_name,
                    :size_sqft,
                    :non_zero_count,
                    :total_value,
                    :avg_non_zero_value,
                    :config::jsonb
                );
                """
            ),
            {
                "regression_run_id": p.regression_run_id,
                "scope": scope,
                "market_name": market_name,
                "size_sqft": size,
                "non_zero_count": non_zero_count,
                "total_value": total_value,
                "avg_non_zero_value": avg_non_zero_value,
                "config": json.dumps(p.to_params_json()),
            },
        )


def run_value_map_job(conn: Connection, p: ValueMapJobParams) -> None:
    """
    Compute median estimated value and value per SF per geo unit and persist.
    """
    # Clear previous rows for scope/market and geo_unit_type.
    conn.execute(
        text(
            """
            DELETE FROM analytics_value_maps
            WHERE scope = :scope
              AND COALESCE(market_name, '') = COALESCE(:market_name, '')
              AND geo_unit_type = :geo_unit_type;
            """
        ),
        {
            "scope": p.scope.scope,
            "market_name": p.scope.market_name,
            "geo_unit_type": p.geo_unit_type,
        },
    )

    date_end = p.date_range_end or pd.Timestamp.today().date()

    sql = """
    WITH address_uniq AS (
        SELECT
            pa.property_id,
            MIN(pa.zip_code) AS zip_code
        FROM property_address AS pa
        GROUP BY pa.property_id
    ),
    base AS (
        SELECT
            h.property_id,
            a.zip_code,
            h.sold_price,
            h.living_sq_ft
        FROM mls_history AS h
        JOIN address_uniq AS a
          ON h.property_id = a.property_id
        WHERE
            h.property_use_standardized = :property_use
            AND h.sold_date >= :date_start
            AND h.sold_date <= :date_end
            AND h.sold_price > 0
            AND h.living_sq_ft > 0
    )
    SELECT
        zip_code AS geo_unit_value,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sold_price) AS estimated_value_median,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sold_price / living_sq_ft) AS estimated_value_per_sf_med,
        COUNT(*) AS sample_size
    FROM base
    GROUP BY zip_code;
    """

    params = {
        "property_use": p.property_use,
        "date_start": p.date_range_start,
        "date_end": date_end,
    }

    rows = list(_run_query(conn, sql, params))
    for r in rows:
        conn.execute(
            text(
                """
                INSERT INTO analytics_value_maps (
                    scope,
                    market_name,
                    geo_unit_type,
                    geo_unit_value,
                    estimated_value_median,
                    estimated_value_per_sf_med,
                    sample_size,
                    params
                )
                VALUES (
                    :scope,
                    :market_name,
                    :geo_unit_type,
                    :geo_unit_value,
                    :estimated_value_median,
                    :estimated_value_per_sf_med,
                    :sample_size,
                    :params::jsonb
                );
                """
            ),
            {
                "scope": p.scope.scope,
                "market_name": p.scope.market_name,
                "geo_unit_type": p.geo_unit_type,
                "geo_unit_value": r["geo_unit_value"],
                "estimated_value_median": r["estimated_value_median"],
                "estimated_value_per_sf_med": r["estimated_value_per_sf_med"],
                "sample_size": r["sample_size"],
                "params": json.dumps(p.to_params_json()),
            },
        )

