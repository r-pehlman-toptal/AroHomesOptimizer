from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.engine import Connection

from src.api.dependencies import db_connection_dependency, cognito_auth_dependency
from src.query_service import queries
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
)

router = APIRouter(
    prefix="/queries",
    tags=["queries"],
    dependencies=[Depends(cognito_auth_dependency)],
)


@router.post("/bed-bath-distribution", response_model=List[BedBathDistributionRow])
def api_bed_bath_distribution(
    params: BedBathDistributionParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[BedBathDistributionRow]:
    """
    Query A: LA Bed/Bath distribution endpoint.
    """
    return queries.bed_bath_distribution(conn, params)


@router.post("/principal-sfr-zone", response_model=List[PrincipalZoneRow])
def api_principal_sfr_zone(
    params: PrincipalZoneParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[PrincipalZoneRow]:
    """
    Query B: Principal detached-SFR zone per city.
    """
    return queries.principal_sfr_zone(conn, params)


@router.post("/lot-size-buckets", response_model=List[LotSizeBucketRow])
def api_lot_size_buckets(
    params: LotSizeBucketsParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[LotSizeBucketRow]:
    """
    Query C: Lot size width/depth bucket counts by ZIP.
    """
    return queries.lot_size_buckets(conn, params)


@router.post("/ranked-zips-ppsf", response_model=List[RankedZipRow])
def api_ranked_zips_ppsf(
    params: RankedZipsParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[RankedZipRow]:
    """
    Query D: Ranked ZIPs by PPSF with trimming and thresholds.
    """
    return queries.ranked_zips_ppsf(conn, params)


# ---- F1 Comps (read-only mode: works without analytics schema) ----

@router.post("/f1/comps", response_model=List[F1CompsRow])
def api_f1_comps(
    params: F1CompsParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[F1CompsRow]:
    """
    F1 Comps: read-only. Uses public tables only (no CREATE required).
    Parameters: zip_code, sale_year (default 2024), limit (default 10), min_comps (default 30), ppsf_min (default 400).
    """
    return queries.f1_comps(conn, params)


@router.post("/f3/offer-range", response_model=List[F3OfferRangeRow])
def api_f3_offer_range(
    params: F3OfferRangeParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[F3OfferRangeRow]:
    """
    F3 Offer range: read-only. ZIP only; low/base/high PPSF and price from p25/p50/p75.
    Parameters: zip_code, living_sq_ft, sale_year (2024), ppsf_min (400).
    """
    return queries.f3_offer_range(conn, params)


@router.post("/f4/overpay-risk", response_model=List[F4OverpayRiskRow])
def api_f4_overpay_risk(
    params: F4OverpayRiskParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[F4OverpayRiskRow]:
    """
    F4 Overpay risk: read-only. ZIP only; list_price vs comp-based value; pct above and risk level.
    Parameters: zip_code, list_price, living_sq_ft, sale_year (2024), ppsf_min (400).
    """
    return queries.f4_overpay_risk(conn, params)


# ---- Week 2: Comps, PPSF map, offer range, overpay risk ----

@router.post("/comps", response_model=List[CompsRow])
def api_comps(
    params: CompsParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[CompsRow]:
    """
    Comparable sales by ZIP or by lat/lon (0.25-mi cell). LA, 2020+, ppsf>=400.
    """
    return queries.comps(conn, params)


@router.post("/ppsf-map", response_model=List[PpsfMapRow])
def api_ppsf_map(
    params: PpsfMapParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[PpsfMapRow]:
    """
    PPSF map: grid or ZIP level with median_ppsf, comp_count, confidence_band.
    """
    return queries.ppsf_map(conn, params)


@router.post("/offer-range", response_model=List[OfferRangeRow])
def api_offer_range(
    params: OfferRangeParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[OfferRangeRow]:
    """
    Recommended offer range (low/base/high) from 25th/50th/75th PPSF × living_sq_ft.
    """
    return queries.offer_range(conn, params)


@router.post("/overpay-risk", response_model=List[OverpayRiskRow])
def api_overpay_risk(
    params: OverpayRiskParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[OverpayRiskRow]:
    """
    Overpay risk: list price vs comp-based value; pct above and risk level.
    """
    return queries.overpay_risk(conn, params)


@router.post("/confidence-coverage", response_model=List[ConfidenceCoverageRow])
def api_confidence_coverage(
    params: ConfidenceCoverageParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[ConfidenceCoverageRow]:
    """
    Confidence and coverage: comp_count, confidence_band, effective tier, message.
    """
    return queries.confidence_coverage(conn, params)

