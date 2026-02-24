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

