from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Connection

from src.analytics.jobs import (
    run_lot_heatmap_job,
    run_regression_job,
    run_home_size_scenarios,
    run_value_map_job,
)
from src.analytics.schemas import (
    ScopeConfig,
    LotHeatmapJobParams,
    RegressionJobParams,
    ScenarioJobParams,
    ValueMapJobParams,
)
from src.api.dependencies import db_connection_dependency, cognito_auth_dependency


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(cognito_auth_dependency)],
)


# ---------- Pydantic response models ----------


class RegressionRunSummary(BaseModel):
    id: int
    scope: str
    market_name: Optional[str]
    coef_sqft: float
    intercept: float
    r_squared: Optional[float]
    sample_size: int
    date_range_start: Optional[date]
    date_range_end: Optional[date]


class HomeSizeScenarioRow(BaseModel):
    size_sqft: int
    non_zero_count: int
    total_value: float
    avg_non_zero_value: float


class LotHeatmapRow(BaseModel):
    geo_unit_value: str
    width_bucket_ft: Optional[int]
    depth_bucket_ft: Optional[int]
    lot_size_bucket_sqft: Optional[int]
    lot_count: int
    missing_geom_count: int


class ValueMapRow(BaseModel):
    geo_unit_value: str
    estimated_value_median: float
    estimated_value_per_sf_med: float
    sample_size: int


# ---------- Job trigger endpoints ----------


class ScopeBody(BaseModel):
    scope: str = "county_wide"
    market_name: Optional[str] = None
    counties: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    zips: Optional[List[str]] = None

    def to_scope_config(self) -> ScopeConfig:
        return ScopeConfig(
            scope=self.scope,
            market_name=self.market_name,
            counties=self.counties,
            cities=self.cities,
            zips=self.zips,
        )


class LotHeatmapJobBody(BaseModel):
    scope: ScopeBody
    geo_unit_type: str = "zip"
    bucket_mode: str = "width_depth"
    width_bucket_ft: int = 5
    depth_bucket_ft: int = 5
    lot_size_bucket_sqft: int = 500


@router.post("/run/lot-heatmap")
def api_run_lot_heatmap_job(
    body: LotHeatmapJobBody,
    conn: Connection = Depends(db_connection_dependency),
) -> Dict[str, Any]:
    params = LotHeatmapJobParams(
        scope=body.scope.to_scope_config(),
        geo_unit_type=body.geo_unit_type,
        bucket_mode=body.bucket_mode,
        width_bucket_ft=body.width_bucket_ft,
        depth_bucket_ft=body.depth_bucket_ft,
        lot_size_bucket_sqft=body.lot_size_bucket_sqft,
    )
    run_lot_heatmap_job(conn, params)
    return {"status": "ok"}


class RegressionJobBody(BaseModel):
    scope: ScopeBody
    date_range_start: date = date(2015, 1, 1)
    date_range_end: Optional[date] = None
    property_use: str = "SINGLE FAMILY RESIDENCE"
    min_ppsf: float = 100.0
    max_ppsf: float = 5000.0


@router.post("/run/regression", response_model=RegressionRunSummary)
def api_run_regression_job(
    body: RegressionJobBody,
    conn: Connection = Depends(db_connection_dependency),
) -> RegressionRunSummary:
    params = RegressionJobParams(
        scope=body.scope.to_scope_config(),
        date_range_start=body.date_range_start,
        date_range_end=body.date_range_end,
        property_use=body.property_use,
        min_ppsf=body.min_ppsf,
        max_ppsf=body.max_ppsf,
    )
    run_id = run_regression_job(conn, params)

    res = conn.execute(
        text(
            """
            SELECT
                id,
                scope,
                market_name,
                coef_sqft,
                intercept,
                r_squared,
                sample_size,
                date_range_start,
                date_range_end
            FROM analytics_regression_runs
            WHERE id = :id;
            """
        ),
        {"id": run_id},
    )
    row = res.mappings().one()
    return RegressionRunSummary(**row)


class ScenarioJobBody(BaseModel):
    regression_run_id: int
    size_min: int = 2000
    size_max: int = 3000
    size_step: int = 100


@router.post("/run/home-size-scenarios")
def api_run_scenarios_job(
    body: ScenarioJobBody,
    conn: Connection = Depends(db_connection_dependency),
) -> Dict[str, Any]:
    params = ScenarioJobParams(
        regression_run_id=body.regression_run_id,
        size_min=body.size_min,
        size_max=body.size_max,
        size_step=body.size_step,
    )
    run_home_size_scenarios(conn, params)
    return {"status": "ok"}


class ValueMapJobBody(BaseModel):
    scope: ScopeBody
    geo_unit_type: str = "zip"
    date_range_start: date = date(2015, 1, 1)
    date_range_end: Optional[date] = None
    property_use: str = "SINGLE FAMILY RESIDENCE"


@router.post("/run/value-map")
def api_run_value_map_job(
    body: ValueMapJobBody,
    conn: Connection = Depends(db_connection_dependency),
) -> Dict[str, Any]:
    params = ValueMapJobParams(
        scope=body.scope.to_scope_config(),
        geo_unit_type=body.geo_unit_type,
        date_range_start=body.date_range_start,
        date_range_end=body.date_range_end,
        property_use=body.property_use,
    )
    run_value_map_job(conn, params)
    return {"status": "ok"}


# ---------- Fetch endpoints ----------


@router.get("/regression-runs/{run_id}", response_model=RegressionRunSummary)
def api_get_regression_run(
    run_id: int,
    conn: Connection = Depends(db_connection_dependency),
) -> RegressionRunSummary:
    res = conn.execute(
        text(
            """
            SELECT
                id,
                scope,
                market_name,
                coef_sqft,
                intercept,
                r_squared,
                sample_size,
                date_range_start,
                date_range_end
            FROM analytics_regression_runs
            WHERE id = :id;
            """
        ),
        {"id": run_id},
    )
    row = res.mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="regression run not found")
    return RegressionRunSummary(**row)


@router.get("/home-size-scenarios", response_model=List[HomeSizeScenarioRow])
def api_get_home_size_scenarios(
    regression_run_id: int = Query(...),
    conn: Connection = Depends(db_connection_dependency),
):
    res = conn.execute(
        text(
            """
            SELECT
                size_sqft,
                non_zero_count,
                total_value,
                avg_non_zero_value
            FROM analytics_home_size_scenarios
            WHERE regression_run_id = :id
            ORDER BY size_sqft;
            """
        ),
        {"id": regression_run_id},
    )
    rows = [HomeSizeScenarioRow(**r) for r in res.mappings().all()]
    return rows


@router.get("/lot-heatmap", response_model=List[LotHeatmapRow])
def api_get_lot_heatmap(
    scope: str = Query(...),
    market_name: Optional[str] = Query(None),
    geo_unit_type: str = Query("zip"),
    conn: Connection = Depends(db_connection_dependency),
):
    res = conn.execute(
        text(
            """
            SELECT
                geo_unit_value,
                width_bucket_ft,
                depth_bucket_ft,
                lot_size_bucket_sqft,
                lot_count,
                missing_geom_count
            FROM analytics_lot_heatmap
            WHERE scope = :scope
              AND COALESCE(market_name, '') = COALESCE(:market_name, '')
              AND geo_unit_type = :geo_unit_type;
            """
        ),
        {
            "scope": scope,
            "market_name": market_name,
            "geo_unit_type": geo_unit_type,
        },
    )
    rows = [LotHeatmapRow(**r) for r in res.mappings().all()]
    return rows


@router.get("/value-maps", response_model=List[ValueMapRow])
def api_get_value_maps(
    scope: str = Query(...),
    market_name: Optional[str] = Query(None),
    geo_unit_type: str = Query("zip"),
    conn: Connection = Depends(db_connection_dependency),
):
    res = conn.execute(
        text(
            """
            SELECT
                geo_unit_value,
                estimated_value_median,
                estimated_value_per_sf_med,
                sample_size
            FROM analytics_value_maps
            WHERE scope = :scope
              AND COALESCE(market_name, '') = COALESCE(:market_name, '')
              AND geo_unit_type = :geo_unit_type;
            """
        ),
        {
            "scope": scope,
            "market_name": market_name,
            "geo_unit_type": geo_unit_type,
        },
    )
    rows = [ValueMapRow(**r) for r in res.mappings().all()]
    return rows

