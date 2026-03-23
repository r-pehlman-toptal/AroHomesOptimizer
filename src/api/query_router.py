from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.engine import Connection

from src.api.dependencies import db_connection_dependency, cognito_auth_dependency
from src.query_service import queries
from src.attom.client import fetch_rebuild_features
from src.query_service.schemas import (
    AddressLookupParams,
    AddressLookupRow,
    BedBathDistributionParams,
    BedBathDistributionRow,
    AttomImprovementLot,
    RebuildEvalCompsEconomics,
    RebuildEvalParams,
    RebuildEvalResponse,
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
    RegionLotSizesParams,
    RegionLotSizesRow,
    RegionHomeSizesParams,
    RegionHomeSizesRow,
    RegionHomeLotSizesParams,
    RegionHomeLotSizesRow,
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


@router.post("/comps-aggregate", response_model=List[CompsAggregateRow])
def api_comps_aggregate(
    params: CompsAggregateParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[CompsAggregateRow]:
    """
    How much – aggregate: comp set with hard filters (12-month recency, distance cap, size band, property_subtype)
    and soft weights. Returns one row: comp_count, median_ppsf, p25/p75, iqr, median_dom, similarity diagnostics,
    confidence_score (0–1) and confidence_band (low/med/high).
    """
    return queries.comps_aggregate(conn, params)


@router.post("/comps-aggregate-rows", response_model=List[CompsAggregateCompRow])
def api_comps_aggregate_rows(
    params: CompsAggregateParams,
    conn: Connection = Depends(db_connection_dependency),
    limit: int = Query(50, ge=1, le=100, description="Max comp rows to return."),
) -> List[CompsAggregateCompRow]:
    """
    Row-level comps with weights (same filters as comps-aggregate). Each row has dist_miles, months_ago, w.
    Use limit query param to cap rows (default 50, max 100).
    """
    return queries.comps_aggregate_rows(conn, params, limit=limit)


@router.post("/zoning-summary", response_model=List[ZoningSummaryRow])
def api_zoning_summary(
    params: ZoningSummaryParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[ZoningSummaryRow]:
    """
    Week 3: Zoning summary ("what you can build") for one parcel.
    Returns zone_code, lot_size_sq_ft, max_gfa_estimate, max_height_ft, min_parking_spaces, max_units from zone lookup.
    """
    return queries.zoning_summary(conn, params)


@router.post("/parcel-center", response_model=List[ParcelCenterRow])
def api_parcel_center(
    params: ParcelCenterParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[ParcelCenterRow]:
    """
    Week 3: Parcel center point (WGS84) for proximity to essentials. Use with external POI.
    """
    return queries.parcel_center(conn, params)


@router.post("/parcel-footprint", response_model=List[ParcelFootprintRow])
def api_parcel_footprint(
    params: ParcelFootprintParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[ParcelFootprintRow]:
    """
    Lot footprint for one parcel: width, depth, width-to-depth ratio, ratio_band (narrow | balanced | wide).
    Focus on home footprint for ideal economics.
    """
    return queries.parcel_footprint(conn, params)


@router.post("/property-info", response_model=List[PropertyInfoRow])
def api_property_info(
    params: PropertyInfoParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[PropertyInfoRow]:
    """
    Latest mls_history row for one property_id: sold_date, sold_price, living_sq_ft, zip, city.
    Use to pre-fill subject when selecting a property by ID.
    """
    return queries.property_info(conn, params)


@router.post("/address-lookup", response_model=List[AddressLookupRow])
def api_address_lookup(
    params: AddressLookupParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[AddressLookupRow]:
    """
    Resolve address text to up to 5 candidate property_ids.
    Numeric address_text is treated as property_id; otherwise provide zip_code and/or city_name.
    """
    return queries.address_lookup(conn, params)


@router.post("/rebuild-eval", response_model=RebuildEvalResponse)
def api_rebuild_eval(
    params: RebuildEvalParams,
    conn: Connection = Depends(db_connection_dependency),
) -> RebuildEvalResponse:
    """
    Rebuild evaluation: resolve address, then property info, parcel footprint, zoning, comps.
    Returns feasibility_fit (max_gfa, fits_target_sq_ft) and comps_economics. is_valid=false when data missing.
    When MLS has no sale (existing_value null), falls back to Attom suggested_existing_value if resolved_address is set.
    """
    result = queries.rebuild_eval(conn, params)
    # Attom: existing_value fallback when MLS has no sale, and improvement + lot for Rebuild tab
    if result.resolved_address:
        try:
            attom = fetch_rebuild_features(result.resolved_address.strip(), target_living_sq_ft=params.target_living_sq_ft)
        except Exception:
            attom = {}
        feats = attom.get("rebuild_features") or {}
        updates = {}
        # Fallback existing_value when MLS null
        if (
            result.comps_economics is not None
            and result.comps_economics.existing_value is None
        ):
            ev = feats.get("suggested_existing_value")
            if ev is not None:
                try:
                    ev_float = float(ev)
                except (TypeError, ValueError):
                    ev_float = None
                if ev_float is not None:
                    base = result.comps_economics.newbuild_value_base
                    value_accretion = (base - ev_float) if base is not None else None
                    try:
                        updates["comps_economics"] = RebuildEvalCompsEconomics(
                            **(
                                result.comps_economics.model_dump()
                                | {"existing_value": ev_float, "existing_value_source": "attom", "value_accretion": value_accretion}
                            )
                        )
                    except Exception:
                        pass
        # Attom improvement + lot for UI (next to DB property_info/footprint)
        def _safe_int(v):
            if v is None:
                return None
            try:
                return int(float(v))
            except (TypeError, ValueError):
                return None

        def _safe_float(v):
            if v is None:
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        if any(feats.get(k) is not None for k in ("living_sq_ft", "year_built", "beds", "baths", "lot_sq_ft")):
            try:
                updates["attom_improvement_lot"] = AttomImprovementLot(
                    living_sq_ft=_safe_float(feats.get("living_sq_ft")),
                    year_built=_safe_int(feats.get("year_built")),
                    beds=_safe_int(feats.get("beds")),
                    baths=_safe_int(feats.get("baths")),
                    lot_sq_ft=_safe_float(feats.get("lot_sq_ft")),
                )
            except Exception:
                pass
        if updates:
            try:
                result = result.model_copy(update=updates)
            except Exception:
                pass
    return result


@router.post("/region-lot-sizes", response_model=List[RegionLotSizesRow])
def api_region_lot_sizes(
    params: RegionLotSizesParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[RegionLotSizesRow]:
    """
    Lot sizes for parcels in a region (city + optional ZIP). For lot-size heatmap.
    """
    return queries.region_lot_sizes(conn, params)


@router.post("/region-home-sizes", response_model=List[RegionHomeSizesRow])
def api_region_home_sizes(
    params: RegionHomeSizesParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[RegionHomeSizesRow]:
    """
    Home sizes (living_sq_ft) for sales in a region. For home-size heatmap by year built.
    """
    return queries.region_home_sizes(conn, params)


@router.post("/region-home-lot-sizes", response_model=List[RegionHomeLotSizesRow])
def api_region_home_lot_sizes(
    params: RegionHomeLotSizesParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[RegionHomeLotSizesRow]:
    """
    Home size × lot size for sales in a region. For 2D heatmap.
    """
    return queries.region_home_lot_sizes(conn, params)


@router.post("/nearby-zoning", response_model=List[NearbyZoningRow])
def api_nearby_zoning(
    params: NearbyZoningParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[NearbyZoningRow]:
    """
    Week 3: Nearby zoning display. Subject parcel + other parcels in same ZIP with zone(s).
    """
    return queries.nearby_zoning(conn, params)


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


@router.post("/volume-by-zip-year", response_model=List[VolumeByZipYearRow])
def api_volume_by_zip_year(
    params: VolumeByZipYearParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[VolumeByZipYearRow]:
    """Volume by ZIP × year for web viz: sale_count, median_ppsf, median_dom."""
    return queries.volume_by_zip_year(conn, params)


@router.post("/volume-by-city-year", response_model=List[VolumeByCityYearRow])
def api_volume_by_city_year(
    params: VolumeByCityYearParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[VolumeByCityYearRow]:
    """Volume by city × year: total_sales, median_ppsf, avg_ppsf."""
    return queries.volume_by_city_year(conn, params)


@router.post("/volume-by-zip-month", response_model=List[VolumeByZipMonthRow])
def api_volume_by_zip_month(
    params: VolumeByZipMonthParams,
    conn: Connection = Depends(db_connection_dependency),
) -> List[VolumeByZipMonthRow]:
    """Volume by ZIP × month for seasonality viz."""
    return queries.volume_by_zip_month(conn, params)

