"""Rebuild decision system: feasibility, product→areas, portfolio ranking."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.engine import Connection

from src.api.dependencies import db_connection_dependency, cognito_auth_dependency
from src.query_service import queries
from src.query_service.feasibility_engine import run_feasibility_check
from src.query_service.portfolio_ranking import portfolio_rank
from src.query_service.product_ranking import product_areas_ranking
from src.query_service.schemas import (
    AreaRankingRow,
    FeasibilityCheckParams,
    FeasibilityCheckResult,
    NewBuildBenchmarkParams,
    NewBuildBenchmarkRow,
    PortfolioRankParams,
    PortfolioRankRow,
    ProductWhereToBuildParams,
    SiteSearchParams,
    SiteSearchRow,
    TargetPipelineSummary,
    TargetPipelineSummaryParams,
)


router = APIRouter(
    prefix="/decisions",
    tags=["decisions"],
    dependencies=[Depends(cognito_auth_dependency)],
)


@router.post("/feasibility", response_model=FeasibilityCheckResult)
def api_feasibility(
    params: FeasibilityCheckParams,
    conn: Connection = Depends(db_connection_dependency),
) -> FeasibilityCheckResult:
    """
    Parcel-level feasibility: can we build the target product here?
    Returns pass/fail, reason codes, recommended size band, and expected price/DOM when pass.
    """
    return run_feasibility_check(conn, params)


@router.post("/product-areas", response_model=List[AreaRankingRow])
def api_product_areas(
    params: ProductWhereToBuildParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[AreaRankingRow]:
    """
    Product → where to build: ranked ZIPs or submarkets for target size/product type.
    Returns median PPSF, DOM, supply count, and composite score per area.
    """
    return product_areas_ranking(conn, params)


@router.post("/new-build-benchmark", response_model=List[NewBuildBenchmarkRow])
def api_new_build_benchmark(
    params: NewBuildBenchmarkParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[NewBuildBenchmarkRow]:
    """
    New-build benchmark: PPSF and DOM distributions (p25/p50/p75) for recent new builds by area.
    """
    return queries.new_build_benchmark(conn, params)


@router.post("/site-search", response_model=List[SiteSearchRow])
def api_site_search(
    params: SiteSearchParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[SiteSearchRow]:
    """
    Site search: given target sqft and optional footprint constraints, return parcels where
    zoning × lot size × dimensions could support building that product (no starting property_id required).
    """
    return queries.site_search(conn, params)


@router.post("/target-pipeline-summary", response_model=TargetPipelineSummary)
def api_target_pipeline_summary(
    params: TargetPipelineSummaryParams,
    conn: Connection = Depends(db_connection_dependency),
) -> TargetPipelineSummary:
    """
    Target pipeline: same filters as site search (target sqft, city, ZIP, 50-yr-old, ~1,400 sq ft).
    Returns parcel count and aggregate value created (new-build value − existing) for that product.
    """
    return queries.target_pipeline_summary(conn, params)


@router.post("/portfolio-rank", response_model=List[PortfolioRankRow])
def api_portfolio_rank(
    params: PortfolioRankParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[PortfolioRankRow]:
    """
    Portfolio ranking: run feasibility + economics for each parcel, return ranked list with drivers and low-confidence flags.
    """
    return portfolio_rank(conn, params)
