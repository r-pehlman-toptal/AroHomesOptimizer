"""
Rebuild decision system: binary feasibility gate for a parcel + target product.
Uses parcel footprint, zoning summary, and comps aggregate. Emits reason codes for explainability.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.engine import Connection

from src.query_service import queries
from src.economics.cost_model import CostModelParams, compute_scenarios
from src.query_service.explainability import build_reason_messages
from src.query_service.schemas import (
    CompsAggregateParams,
    CompsAggregateRow,
    FeasibilityCheckParams,
    FeasibilityCheckResult,
    ParcelFootprintParams,
    ParcelFootprintRow,
    PropertyInfoParams,
    ZoningSummaryParams,
    ZoningSummaryRow,
)


def _norm_city(city_name: str | None) -> str:
    s = (city_name or "").strip()
    return s.upper() if s else "LOS ANGELES"


# Minimum lot dimension (ft) to fit a given building sqft; assumes ~single-story footprint and aspect <= 2.
# min_side >= sqrt(sqft / 2) with buffer; we use 0.85 factor for setbacks/simple shape.
def _min_lot_dimension_for_sqft(sqft: float) -> float:
    from math import sqrt
    buildable = sqft  # assume 1 story for simplicity
    min_side = sqrt(buildable / 2.0)  # rectangle aspect 2
    return round(min_side * 1.15, 1)  # 15% buffer


def _footprint_ratio_band_from_dims(w: float, d: float) -> str:
    """Orientation-free ratio band from width/depth (same logic as queries._footprint_ratio_band)."""
    if not w or not d:
        return "balanced"
    lo, hi = min(w, d), max(w, d)
    ratio = hi / lo
    if ratio <= 1.3:
        return "balanced"
    if ratio <= 2.0:
        return "moderate"
    return "extreme"


def _fail_result_with_messages(
    p: FeasibilityCheckParams,
    reason_codes: List[str],
    fp: ParcelFootprintRow | None,
    zon: ZoningSummaryRow | None,
    comps: CompsAggregateRow | None,
) -> FeasibilityCheckResult:
    min_dim = _min_lot_dimension_for_sqft(p.target_sqft)
    lot_w = (p.lot_width_ft if p.lot_width_ft is not None and p.lot_width_ft > 0 else None) or (fp.lot_width_ft if fp else None) or 0
    lot_d = (p.lot_depth_ft if p.lot_depth_ft is not None and p.lot_depth_ft > 0 else None) or (fp.lot_depth_ft if fp else None) or 0
    context = {
        "target_sqft": p.target_sqft,
        "required_width_ft": min_dim,
        "required_depth_ft": min_dim,
        "lot_width_ft": lot_w,
        "lot_depth_ft": lot_d,
        "max_gfa_estimate": (zon.max_gfa_estimate or 0) if zon else 0,
    }
    reason_messages = build_reason_messages(reason_codes, context)
    return _result_fail(p, reason_codes, fp, zon, comps, reason_messages)


def run_feasibility_check(conn: Connection, p: FeasibilityCheckParams) -> FeasibilityCheckResult:
    """
    Binary feasibility gate for parcel + target product. Loads footprint, zoning, comps;
    returns pass/fail, reason codes, recommended band, and economics when pass.
    """
    reason_codes: List[str] = []
    city = _norm_city(p.city_name)

    # 1) Parcel footprint (or use UI overrides when dimensions missing)
    fp_rows = queries.parcel_footprint(conn, ParcelFootprintParams(property_id=p.property_id))
    fp: ParcelFootprintRow = fp_rows[0] if fp_rows else None
    use_override = (
        p.lot_width_ft is not None and p.lot_width_ft > 0
        and p.lot_depth_ft is not None and p.lot_depth_ft > 0
    )
    if not fp or not fp.is_valid_dimensions:
        if use_override:
            w = float(p.lot_width_ft)
            d = float(p.lot_depth_ft)
        else:
            reason_codes.append("footprint_data_missing")
            return _fail_result_with_messages(p, reason_codes, fp, None, None)
    else:
        w = fp.lot_width_ft or 0
        d = fp.lot_depth_ft or 0
        if use_override:
            w = float(p.lot_width_ft)
            d = float(p.lot_depth_ft)

    # 2) Zoning summary
    zon_rows = queries.zoning_summary(conn, ZoningSummaryParams(parcel_id=p.property_id))
    zon: ZoningSummaryRow = zon_rows[0] if zon_rows else None
    if not zon:
        reason_codes.append("zoning_data_missing")
        return _fail_result_with_messages(p, reason_codes, fp, None, None)
    if zon.max_gfa_estimate is None and zon.zone_code:
        reason_codes.append("insufficient_far")
        return _fail_result_with_messages(p, reason_codes, fp, zon, None)
    if zon.max_gfa_estimate is not None and p.target_sqft > zon.max_gfa_estimate:
        reason_codes.append("target_exceeds_max_gfa")
        return _fail_result_with_messages(p, reason_codes, fp, zon, None)

    # 3) Lot dimensions vs required for target (w, d from footprint or overrides)
    min_dim = _min_lot_dimension_for_sqft(p.target_sqft)
    if w < min_dim:
        reason_codes.append("width_too_narrow")
    if d < min_dim:
        reason_codes.append("depth_too_shallow")
    if reason_codes:
        return _fail_result_with_messages(p, reason_codes, fp, zon, None)

    # 4) Comps & economics (use property city if not provided)
    if not p.city_name:
        info_rows = queries.property_info(conn, PropertyInfoParams(property_id=p.property_id))
        if info_rows and info_rows[0].city_name:
            city = _norm_city(info_rows[0].city_name)
    comps_params = CompsAggregateParams(
        subject_parcel_id=p.property_id,
        subject_sqft=p.target_sqft,
        property_subtype=p.product_type or "SINGLE FAMILY RESIDENCE",
        distance_cap_miles=2.0,
        size_band_pct=0.2,
        recency_months=12,
        ppsf_min=400.0,
        city_name=city,
    )
    comps_rows: List[CompsAggregateRow] = queries.comps_aggregate(conn, comps_params)
    comps = comps_rows[0] if comps_rows else None
    if comps and comps.comp_count == 0:
        reason_codes.append("insufficient_comps")
        return _fail_result_with_messages(p, reason_codes, fp, zon, comps)

    # Pass: build result with recommended band, economics, and scenarios (use fp.ratio_band when from footprint)
    size_low = max(0, p.target_sqft - 300)
    size_high = p.target_sqft + 300
    ratio_band = fp.ratio_band if fp and fp.ratio_band else (_footprint_ratio_band_from_dims(w, d) if w and d else None)
    base, downside, upside = compute_scenarios(
        p.target_sqft,
        comps.median_ppsf or 0,
        comps.p25_ppsf,
        comps.p75_ppsf,
        CostModelParams(),
    )
    return FeasibilityCheckResult(
        property_id=p.property_id,
        target_sqft=p.target_sqft,
        pass_fail=True,
        reason_codes=[],
        recommended_size_band_low=size_low,
        recommended_size_band_high=size_high,
        recommended_footprint_band=ratio_band,
        max_gfa_estimate=zon.max_gfa_estimate,
        expected_p25_ppsf=comps.p25_ppsf if comps else None,
        expected_p50_ppsf=comps.median_ppsf if comps else None,
        expected_p75_ppsf=comps.p75_ppsf if comps else None,
        expected_p25_price=(comps.p25_ppsf * p.target_sqft) if comps and comps.p25_ppsf else None,
        expected_p50_price=(comps.median_ppsf * p.target_sqft) if comps and comps.median_ppsf else None,
        expected_p75_price=(comps.p75_ppsf * p.target_sqft) if comps and comps.p75_ppsf else None,
        expected_median_dom=comps.median_dom if comps else None,
        expected_p75_dom=comps.p75_dom if comps else None,
        comp_count=comps.comp_count if comps else 0,
        confidence_band=comps.confidence_band if comps else None,
        confidence_explanation=_confidence_explanation(comps),
        scenario_base_margin_pct=round(base.margin_pct, 2),
        scenario_downside_margin_pct=round(downside.margin_pct, 2),
        scenario_upside_margin_pct=round(upside.margin_pct, 2),
        scenario_base_irr=round(base.irr_proxy, 4),
        scenario_downside_irr=round(downside.irr_proxy, 4),
        scenario_upside_irr=round(upside.irr_proxy, 4),
    )


def _result_fail(
    p: FeasibilityCheckParams,
    reason_codes: List[str],
    fp: ParcelFootprintRow | None,
    zon: ZoningSummaryRow | None,
    comps: CompsAggregateRow | None,
    reason_messages: List[str] | None = None,
) -> FeasibilityCheckResult:
    return FeasibilityCheckResult(
        property_id=p.property_id,
        target_sqft=p.target_sqft,
        pass_fail=False,
        reason_codes=reason_codes,
        reason_messages=reason_messages or [],
        recommended_size_band_low=None,
        recommended_size_band_high=None,
        recommended_footprint_band=fp.ratio_band if fp else None,
        max_gfa_estimate=zon.max_gfa_estimate if zon else None,
        expected_p25_ppsf=comps.p25_ppsf if comps else None,
        expected_p50_ppsf=comps.median_ppsf if comps else None,
        expected_p75_ppsf=comps.p75_ppsf if comps else None,
        expected_p25_price=(comps.p25_ppsf * p.target_sqft) if comps and comps.p25_ppsf else None,
        expected_p50_price=(comps.median_ppsf * p.target_sqft) if comps and comps.median_ppsf else None,
        expected_p75_price=(comps.p75_ppsf * p.target_sqft) if comps and comps.p75_ppsf else None,
        expected_median_dom=comps.median_dom if comps else None,
        expected_p75_dom=comps.p75_dom if comps else None,
        comp_count=comps.comp_count if comps else 0,
        confidence_band=comps.confidence_band if comps else None,
        confidence_explanation=_confidence_explanation(comps),
    )


def _confidence_explanation(comps: CompsAggregateRow | None) -> str | None:
    if not comps or comps.comp_count == 0:
        return None
    band = (comps.confidence_band or "low").lower()
    return f"Based on {comps.comp_count} comps; confidence {band}."
