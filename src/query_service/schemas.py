from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, root_validator, validator

# ---- Rebuild decision system: reason codes (explainability) ----
FEASIBILITY_REASON_CODES = (
    "width_too_narrow",
    "depth_too_shallow",
    "insufficient_far",
    "insufficient_comps",
    "missing_geometry",
    "zoning_data_missing",
    "target_exceeds_max_gfa",
    "footprint_data_missing",
)


class BedBathDistributionParams(BaseModel):
    city: str = Field(default="LOS ANGELES", description="Target city, case-insensitive.")
    min_sold_date: date = Field(default=date(2015, 1, 1))
    min_year_built: int = Field(default=2015)
    min_ppsf: float = Field(default=900.0)
    min_living_sqft: int = Field(default=2400)
    max_living_sqft: int = Field(default=3200)
    min_beds: int = Field(default=4)
    max_beds: int = Field(default=6)
    min_full_baths: int = Field(default=3)
    max_full_baths: int = Field(default=5)
    allowed_half_baths: List[int] = Field(default_factory=lambda: [0, 1])
    property_use: str = Field(
        default="SINGLE FAMILY RESIDENCE",
        description="Standardized SFR label in mls_history.property_use_standardized.",
    )

    @validator("city")
    def normalize_city(cls, v: str) -> str:
        return v.upper()


class BedBathDistributionRow(BaseModel):
    living_sqft_bucket: int
    beds: int
    baths_full: int
    baths_half: int
    sale_count: int
    median_price_per_sqft: float
    median_sold_price: float


class PrincipalZoneParams(BaseModel):
    cities: List[str] = Field(..., description="List of city names, case-insensitive.")
    min_parcels: int = Field(default=100)

    @validator("cities", each_item=True)
    def normalize_city(cls, v: str) -> str:
        return v.upper()


class PrincipalZoneRow(BaseModel):
    city_name: str
    zoning_code: str
    parcel_count: int


class LotSizeBucketsParams(BaseModel):
    zip_codes: Optional[List[str]] = Field(
        default=None, description="Optional list of ZIP codes to restrict to."
    )
    bucket_size_ft: int = Field(default=5, description="Width/depth bucket size in feet.")
    property_subtype: Optional[str] = Field(
        default=None, description="Optional property_use_standardized filter (e.g. SINGLE FAMILY RESIDENCE)."
    )
    min_lot_size_sq_ft: Optional[float] = Field(default=None, description="Optional minimum lot_size_sq_ft.")
    max_lot_size_sq_ft: Optional[float] = Field(default=None, description="Optional maximum lot_size_sq_ft.")
    exclude_outliers: bool = Field(
        default=False,
        description="If true, exclude extreme width/depth (e.g. outside 10–250 ft).",
    )


class LotSizeBucketRow(BaseModel):
    zip_code: str
    width_bucket: int
    depth_bucket: int
    lot_count: int


class RankedZipsParams(BaseModel):
    min_sold_date: date = Field(default=date(2015, 1, 1))
    min_ppsf: float = Field(default=100.0)
    max_ppsf: float = Field(default=5000.0)
    trim_lower_pct: float = Field(default=0.01)
    trim_upper_pct: float = Field(default=0.99)
    min_median_ppsf: float = Field(default=750.0)
    min_sale_count: int = Field(default=20)
    allowed_counties: List[str] = Field(
        default_factory=lambda: ["LOS ANGELES", "ORANGE"],
        description="County names for base sales filter, case-insensitive.",
    )
    property_use: str = Field(
        default="SINGLE FAMILY RESIDENCE",
        description="Standardized SFR label in mls_history.property_use_standardized.",
    )

    @validator("allowed_counties", each_item=True)
    def normalize_county(cls, v: str) -> str:
        return v.upper()


class RankedZipRow(BaseModel):
    zip_code: str
    median_ppsf: float
    avg_living_sqft: float
    sale_count: int


# ---- Week 2: Comps, PPSF map, offer range, overpay risk, confidence ----

# ---- F1 Comps (read-only mode: public tables only; Tableau + web app) ----

class F1CompsParams(BaseModel):
    """F1 Comps: read-only mode. zip_code required; no analytics schema required."""
    zip_code: str = Field(..., min_length=1, description="ZIP code for comps.")
    sale_year: int = Field(default=2024, ge=2020, description="Sale year (used when date/year-built range not set).")
    min_sold_date: Optional[date] = Field(default=None, description="Only sales on or after this date; with max_sold_date defines range.")
    max_sold_date: Optional[date] = Field(default=None, description="Only sales on or before this date; with min_sold_date defines range.")
    min_year_built: Optional[int] = Field(default=None, description="When set with max_year_built, filter by year built instead of sold date.")
    max_year_built: Optional[int] = Field(default=None, description="When set with min_year_built, filter by year built instead of sold date.")
    limit: int = Field(default=10, ge=1, le=50, description="Max comps to return.")
    min_comps: int = Field(default=30, ge=1, description="Minimum cohort size for confidence; used for warnings.")
    ppsf_min: float = Field(default=400.0, ge=0, description="Minimum PPSF filter (LA quality).")
    city_name: str = Field(default="LOS ANGELES", description="City filter (case-insensitive).")


class F1CompsRow(BaseModel):
    """One comp sale row; comp_count and confidence_band are cohort-level (same for all rows)."""
    sale_id: int
    property_id: int
    sold_date: date
    sold_price: float
    living_sq_ft: float
    ppsf: float
    zip_code: Optional[str] = None
    city_name: Optional[str] = None
    year_built: Optional[int] = None
    comp_count: int = Field(description="Total comps in this zip + year cohort.")
    confidence_band: str = Field(description="'low' | 'med' | 'high' based on cohort size.")


class F3OfferRangeParams(BaseModel):
    """F3 Offer range: read-only. ZIP only; p25/p50/p75 PPSF × living_sq_ft."""
    zip_code: str = Field(..., min_length=1)
    living_sq_ft: float = Field(gt=0)
    sale_year: int = Field(default=2024, ge=2020)
    ppsf_min: float = Field(default=400.0, ge=0)
    city_name: str = Field(default="LOS ANGELES", description="City filter (case-insensitive).")


class F3OfferRangeRow(BaseModel):
    low_ppsf: float
    base_ppsf: float
    high_ppsf: float
    low_price: float
    base_price: float
    high_price: float
    comp_count: int
    geography_used: str


class F4OverpayRiskParams(BaseModel):
    """F4 Overpay risk: read-only. ZIP only; list_price vs comp-based value."""
    zip_code: str = Field(..., min_length=1)
    list_price: float = Field(gt=0)
    living_sq_ft: float = Field(gt=0)
    sale_year: int = Field(default=2024, ge=2020)
    ppsf_min: float = Field(default=400.0, ge=0)
    city_name: str = Field(default="LOS ANGELES", description="City filter (case-insensitive).")


class F4OverpayRiskRow(BaseModel):
    comp_median_ppsf: float
    comp_based_value: float
    list_price: float
    pct_above_comps: float
    risk_level: str
    comp_count: int
    geography_used: str


# ---- Comps aggregate (how much: filters + weights + confidence from coverage/proximity/recency/tightness) ----

class CompsAggregateParams(BaseModel):
    """Subject parcel + hard filters + weight half-lives. Rolling 12-month recency, optional distance cap and size band."""
    subject_parcel_id: int = Field(..., gt=0, description="Subject parcel (property_id); used for subject point_3310.")
    subject_sqft: float = Field(..., gt=0, description="Subject living sqft; optional size band is ±size_band_pct around this.")
    property_subtype: Optional[str] = Field(
        default=None,
        description="Filter comps to same property_use_standardized (e.g. SINGLE FAMILY RESIDENCE). None = no filter.",
    )
    distance_cap_miles: float = Field(default=2.0, ge=0.1, le=20.0, description="Max distance for comps (miles).")
    size_band_pct: float = Field(default=0.2, ge=0, le=1.0, description="Size band ±pct around subject_sqft (e.g. 0.2 = ±20%).")
    recency_months: int = Field(default=12, ge=1, le=36, description="Only comps sold in last N months.")
    ppsf_min: float = Field(default=400.0, ge=0, description="Minimum PPSF filter.")
    half_life_months: float = Field(default=6.0, gt=0, description="Recency weight half-life (months).")
    half_life_miles: float = Field(default=0.5, gt=0, description="Proximity weight half-life (miles).")
    city_name: str = Field(default="LOS ANGELES", description="City filter (case-insensitive).")


class CompsAggregateRow(BaseModel):
    """One row: group-level aggregates and similarity diagnostics from weighted comp set."""
    comp_count: int
    median_ppsf: Optional[float] = None
    p25_ppsf: Optional[float] = None
    p75_ppsf: Optional[float] = None
    iqr_ppsf: Optional[float] = None
    median_dom: Optional[float] = None
    p75_dom: Optional[float] = None
    median_dist_miles: Optional[float] = None
    median_months_ago: Optional[float] = None
    pct_within_025mi: Optional[float] = None
    pct_within_05mi: Optional[float] = None
    pct_within_3mo: Optional[float] = None
    pct_within_6mo: Optional[float] = None
    pct_within_20pct_sqft: Optional[float] = None
    match_rate: Optional[float] = Field(default=None, description="% comps same subtype AND within sqft band; alias for pct_within_20pct_sqft.")
    ppsf_spread: Optional[float] = Field(default=None, description="IQR of PPSF (p75 - p25); same as iqr_ppsf.")
    spread_ratio: Optional[float] = Field(default=None, description="IQR / median_ppsf; higher = more inconsistent comps.")
    expected_ppsf: Optional[float] = Field(default=None, description="Predicted PPSF proxy from comps; same as median_ppsf (p50).")
    upside_score: Optional[float] = Field(default=None, description="(p75 - p50) / p50; upside potential vs median.")
    confidence_score: Optional[float] = Field(default=None, description="0–1; from coverage, proximity, recency, tightness.")
    confidence_band: Optional[str] = Field(default=None, description="'low' | 'med' | 'high'.")
    confidence_coverage: Optional[float] = Field(default=None, description="0–1; min(1, comp_count/30).")
    confidence_proximity: Optional[float] = Field(default=None, description="0–1; exp(-median_dist_miles/0.5).")
    confidence_recency: Optional[float] = Field(default=None, description="0–1; exp(-median_months_ago/6).")
    confidence_tightness: Optional[float] = Field(default=None, description="0–1; 1 - min(1, iqr_ppsf/median_ppsf).")
    hint: Optional[str] = Field(default=None, description="When comp_count=0, optional reason (e.g. subject has no geometry).")


class CompsAggregateCompRow(BaseModel):
    """One comp row with weight (row-level from comps_aggregate_rows)."""
    sale_id: int
    property_id: int
    sold_date: date
    sold_price: float
    living_sq_ft: float
    ppsf: float
    days_on_market: Optional[float] = None
    zip_code: Optional[str] = None
    city_name: Optional[str] = None
    dist_miles: float
    months_ago: float
    w: float = Field(description="Weight = recency_weight * proximity_weight.")


# ---- Week 3: Zoning summary ("what you can build") ----

class ZoningSummaryParams(BaseModel):
    """Zoning summary for one parcel. Returns zone + constraint estimates from zone lookup."""
    parcel_id: int = Field(..., gt=0, description="Parcel (property_id) to summarize.")


class ZoningSummaryRow(BaseModel):
    """One row: parcel zoning and derived constraints (max_gfa_estimate, max_height_ft, etc.)."""
    parcel_id: int
    zone_code: Optional[str] = None
    lot_size_sq_ft: Optional[float] = None
    max_gfa_estimate: Optional[float] = None
    max_height_ft: Optional[float] = None
    min_parking_spaces: Optional[float] = None
    max_units: Optional[int] = None


class ParcelCenterParams(BaseModel):
    """Center point (WGS84) for one parcel; for proximity/distance use."""
    parcel_id: int = Field(..., gt=0)


class ParcelFootprintParams(BaseModel):
    """Footprint (width, depth, width-to-depth ratio) for one parcel from property_geometry."""
    property_id: int = Field(..., gt=0)


class ParcelFootprintRow(BaseModel):
    """One row: lot dimensions, orientation-free aspect_ratio, ratio_band; data quality fields."""
    property_id: int
    lot_size_sq_ft: Optional[float] = None
    lot_width_ft: Optional[float] = Field(None, description="Frontage (vendor or inferred). Width = vendor_lot_width_ft.")
    lot_depth_ft: Optional[float] = Field(None, description="Lot depth (vendor or inferred). Depth = vendor_lot_depth_ft.")
    width_to_depth_ratio: Optional[float] = Field(None, description="width / depth (legacy); >1 = wider than deep.")
    aspect_ratio: Optional[float] = Field(None, description="Orientation-free: max(width,depth)/min(width,depth), always >= 1.")
    ratio_band: str = Field(description="'balanced' (1.0–1.3) | 'moderate' (1.3–2.0) | 'extreme' (>2.0).")
    width_source: Optional[str] = Field(None, description="'vendor' | 'inferred'.")
    depth_source: Optional[str] = Field(None, description="'vendor' | 'inferred'.")
    is_valid_dimensions: bool = Field(description="True when both width and depth are present and > 0.")
    notes: Optional[str] = Field(None, description="E.g. 'width missing', 'depth zero', or empty when valid.")


class ParcelCenterRow(BaseModel):
    parcel_id: int
    longitude: float
    latitude: float


class RegionLotSizesParams(BaseModel):
    """Lot sizes for parcels in a region (for lot-size heatmap)."""
    city_name: str = Field(default="LOS ANGELES", description="City filter (case-insensitive).")
    zip_code: Optional[str] = Field(default=None, description="Optional ZIP filter.")
    min_year_built: Optional[int] = Field(default=None, description="If set with max_year_built, only parcels with building built in this range.")
    max_year_built: Optional[int] = Field(default=None, description="If set with min_year_built, only parcels with building built in this range.")
    limit: int = Field(default=5000, ge=1, le=50000, description="Max rows to return.")


class RegionLotSizesRow(BaseModel):
    """One row: lot_size_sq_ft for a parcel in the region."""
    lot_size_sq_ft: float


class RegionHomeSizesParams(BaseModel):
    """Home sizes (living_sq_ft) for sales in a region. For home-size heatmap by year built."""
    zip_code: str = Field(..., min_length=1, description="ZIP code.")
    city_name: str = Field(default="", description="City filter (blank = no city filter).")
    min_year_built: int = Field(..., description="Only sales with year_built >= this.")
    max_year_built: int = Field(..., description="Only sales with year_built <= this.")
    limit: int = Field(default=500, ge=1, le=5000, description="Max rows to return.")
    ppsf_min: float = Field(default=400.0, ge=0, description="Minimum PPSF filter.")


class RegionHomeSizesRow(BaseModel):
    """One row: living_sq_ft for a sale in the region."""
    living_sq_ft: float


class RegionHomeLotSizesParams(BaseModel):
    """Home size × lot size for sales in a region. For 2D heatmap."""
    zip_code: str = Field(..., min_length=1, description="ZIP code.")
    city_name: str = Field(default="", description="City filter (blank = no city filter).")
    min_year_built: int = Field(..., description="Only sales with year_built >= this.")
    max_year_built: int = Field(..., description="Only sales with year_built <= this.")
    limit: int = Field(default=1000, ge=1, le=10000, description="Max rows to return.")
    ppsf_min: float = Field(default=400.0, ge=0, description="Minimum PPSF filter.")


class RegionHomeLotSizesRow(BaseModel):
    """One row: living_sq_ft and lot_size_sq_ft for a sale in the region."""
    living_sq_ft: float
    lot_size_sq_ft: float


class PropertyInfoParams(BaseModel):
    """Look up MLS info for one property (property_id). Returns latest sale from mls_history."""
    property_id: int = Field(..., gt=0)


class PropertyInfoRow(BaseModel):
    """One row: latest mls_history sale for the property, with zip and city."""
    sale_id: int
    property_id: int
    sold_date: date
    sold_price: float
    living_sq_ft: float
    ppsf: float
    days_on_market: Optional[float] = None
    year_built: Optional[int] = None
    property_use_standardized: Optional[str] = None
    zip_code: Optional[str] = None
    city_name: Optional[str] = None


class AddressLookupParams(BaseModel):
    """Resolve address text to candidate property_ids. Optional zip_code and city narrow results."""
    address_text: str = Field(..., min_length=1, description="Address string or property_id (numeric).")
    zip_code: Optional[str] = Field(default=None, description="Optional ZIP to narrow search.")
    city_name: Optional[str] = Field(default=None, description="Optional city to narrow search.")


class AddressLookupRow(BaseModel):
    """One candidate: property_id, full_address, zip_code, city, match_score."""
    property_id: int
    full_address: str
    zip_code: Optional[str] = None
    city_name: Optional[str] = None
    match_score: float = Field(ge=0, le=1, description="1.0 = property_id match, 0.7 = zip+city, 0.5 = zip or city only.")


# ---- Rebuild evaluation (address → property + footprint + zoning + comps) ----


class RebuildEvalParams(BaseModel):
    """Evaluate a parcel for rebuild: resolve address, then footprint, zoning, comps."""
    address_text: str = Field(..., min_length=1, description="Address string or property_id (numeric).")
    target_living_sq_ft: float = Field(default=2700.0, gt=0, description="Target living sqft for feasibility and comps.")
    size_band_pct: float = Field(default=0.2, ge=0, le=1.0, description="Comps size band ±pct around target.")
    comps_recency_months: int = Field(default=12, ge=1, le=36, description="Comps sold in last N months.")
    min_year_built: Optional[int] = Field(
        default=2020,
        description="New-build cutoff for pricing (year_built >= min_year_built). Used with new-build benchmark.",
    )
    build_cost_per_sq_ft: float = Field(
        default=400.0,
        gt=0,
        description="Assumed hard + soft build cost per finished sq ft for economics (value vs cost).",
    )
    zip_code: Optional[str] = Field(default=None, description="Optional ZIP to narrow address lookup.")
    city_name: Optional[str] = Field(default=None, description="Optional city to narrow address lookup.")


class RebuildEvalFeasibilityFit(BaseModel):
    """Feasibility: max GFA estimate and whether target sqft fits."""
    max_gfa_estimate: Optional[float] = None
    fits_target_sq_ft: bool = Field(description="True when max_gfa_estimate is set and >= target_living_sq_ft.")
    fit_notes: Optional[str] = None


class RebuildEvalBuildableFootprint(BaseModel):
    """Buildable pad from lot dimensions minus zone setbacks (front, rear, side)."""
    buildable_width_ft: Optional[float] = Field(None, description="Lot width minus 2× side setback.")
    buildable_depth_ft: Optional[float] = Field(None, description="Lot depth minus front and rear setbacks.")
    buildable_sq_ft: Optional[float] = Field(None, description="buildable_width_ft × buildable_depth_ft.")
    notes: Optional[str] = Field(None, description="e.g. when setbacks exceed lot dimensions.")


class RebuildEvalCompsEconomics(BaseModel):
    """Comps economics: PPSF percentiles, price band, count, confidence."""
    p25_ppsf: Optional[float] = None
    p50_ppsf: Optional[float] = None
    p75_ppsf: Optional[float] = None
    price_low: Optional[float] = Field(None, description="p25_ppsf * target_sqft.")
    price_base: Optional[float] = Field(None, description="p50_ppsf * target_sqft.")
    price_high: Optional[float] = Field(None, description="p75_ppsf * target_sqft.")
    comp_count: int = 0
    confidence_band: Optional[str] = None
    confidence_score: Optional[float] = None
    median_dist_miles: Optional[float] = None
    median_months_ago: Optional[float] = None
    hint: Optional[str] = None
    # New-build pricing (driven by new-build benchmark; negative signal when no new builds)
    newbuild_p25_ppsf: Optional[float] = Field(
        default=None,
        description="25th percentile PPSF from recent new-build sales in this area (year_built >= min_year_built).",
    )
    newbuild_p50_ppsf: Optional[float] = Field(
        default=None,
        description="Median PPSF from recent new-build sales in this area.",
    )
    newbuild_p75_ppsf: Optional[float] = Field(
        default=None,
        description="75th percentile PPSF from recent new-build sales in this area.",
    )
    newbuild_price_low: Optional[float] = Field(
        default=None,
        description="New-build p25_ppsf × target_sqft.",
    )
    newbuild_price_base: Optional[float] = Field(
        default=None,
        description="New-build p50_ppsf × target_sqft (primary new-build value anchor).",
    )
    newbuild_price_high: Optional[float] = Field(
        default=None,
        description="New-build p75_ppsf × target_sqft.",
    )
    newbuild_comp_count: int = Field(
        default=0,
        description="Number of recent new-build comps used for pricing (0 = negative signal).",
    )
    has_newbuild_comps: bool = Field(
        default=False,
        description="True when at least one new-build comp exists in the benchmark; False is a negative pricing signal.",
    )
    # Economics vs existing value and build cost
    existing_value: Optional[float] = Field(
        default=None,
        description="Existing AVM or latest sale price used as baseline value (from property_info.sold_price or Attom).",
    )
    existing_value_source: Optional[str] = Field(
        default=None,
        description="Source of existing_value: 'mls' (property_info.sold_price) or 'attom' (suggested_existing_value).",
    )
    newbuild_value_base: Optional[float] = Field(
        default=None,
        description="Base new-build value from newbuild_price_base.",
    )
    value_accretion: Optional[float] = Field(
        default=None,
        description="New-build base value minus existing_value. Positive = value accretive.",
    )
    build_cost: Optional[float] = Field(
        default=None,
        description="Estimated build cost = build_cost_per_sq_ft × target_living_sq_ft.",
    )
    value_created_vs_build_cost: Optional[float] = Field(
        default=None,
        description="New-build base value minus build_cost (gross economic value created).",
    )
    margin_ratio: Optional[float] = Field(
        default=None,
        description="(newbuild_value_base - build_cost) / build_cost, when both are present.",
    )


class AttomImprovementLot(BaseModel):
    """Attom-sourced improvement and lot (shown next to DB property_info/footprint on Rebuild tab)."""
    living_sq_ft: Optional[float] = None
    year_built: Optional[int] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    lot_sq_ft: Optional[float] = None


class RebuildEvalResponse(BaseModel):
    """Full rebuild evaluation: property, footprint, zoning, feasibility, comps; is_valid and notes when data missing."""
    property_id: Optional[int] = Field(None, description="Resolved property_id; None when address cannot be resolved.")
    resolved_address: Optional[str] = None
    is_valid: bool = Field(description="False when address unresolved, or geometry/zoning missing and needed for feasibility.")
    notes: Optional[str] = Field(None, description="Human-readable notes when is_valid=false or partial data.")
    property_info: Optional[PropertyInfoRow] = None
    parcel_footprint: Optional[ParcelFootprintRow] = None
    attom_improvement_lot: Optional[AttomImprovementLot] = Field(
        None,
        description="Attom improvement (sqft, beds, baths, year built) and lot_sq_ft when available; shown next to DB data.",
    )
    zoning_summary: Optional[ZoningSummaryRow] = None
    buildable_footprint: Optional[RebuildEvalBuildableFootprint] = Field(
        None,
        description="Buildable pad (width × depth) from lot minus zone setbacks; None when lot or zone missing.",
    )
    feasibility_fit: Optional[RebuildEvalFeasibilityFit] = None
    comps_economics: Optional[RebuildEvalCompsEconomics] = None
    f3_offer_range: Optional[dict] = Field(None, description="Optional F3 low/base/high if requested.")
    f4_overpay_risk: Optional[dict] = Field(None, description="Optional F4 overpay risk if requested.")


class NearbyZoningParams(BaseModel):
    """Zoning for subject parcel + nearby parcels (same ZIP)."""
    parcel_id: int = Field(..., gt=0, description="Subject parcel (property_id).")
    limit: int = Field(default=21, ge=1, le=100, description="Max rows (subject + nearby).")


class NearbyZoningRow(BaseModel):
    parcel_id: int
    zip_code: Optional[str] = None
    zone_code: Optional[str] = None
    is_subject: bool


class CompsParams(BaseModel):
    """Location by zip or by lat/lon. Comps from analytics fact (LA, 2020+, ppsf>=400)."""
    zip_code: Optional[str] = Field(default=None, description="ZIP code; use when lat/lon not provided.")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    sale_year: int = Field(default=2024, ge=2020, description="Year of sale for comps.")
    limit: int = Field(default=10, ge=1, le=50)

    @validator("longitude")
    def lat_with_lon(cls, v, values):
        if v is not None and values.get("latitude") is None:
            raise ValueError("latitude required when longitude is provided")
        return v

    @root_validator(skip_on_failure=True)
    def require_zip_or_lat_lon(cls, values):
        zip_code, lat, lon = values.get("zip_code"), values.get("latitude"), values.get("longitude")
        if (zip_code and str(zip_code).strip()) or (lat is not None and lon is not None):
            return values
        raise ValueError("Provide either zip_code or both latitude and longitude")


class CompsRow(BaseModel):
    sale_id: int
    property_id: int
    sold_date: date
    sold_price: float
    living_sq_ft: float
    ppsf: float
    zip_code: Optional[str] = None
    city_name: Optional[str] = None
    year_built: Optional[int] = None


class PpsfMapParams(BaseModel):
    """Grid- or zip-level PPSF and confidence for mapping."""
    sale_year: int = Field(default=2024, ge=2020)
    geography: str = Field(default="grid", description="'grid' (0.25-mi cells) or 'zip'.")
    limit: int = Field(default=500, ge=1, le=2000, description="Max rows (e.g. for map viewport).")
    city_name: Optional[str] = Field(default=None, description="City filter for grid (read-only); uses selected city from UI.")


class PpsfMapRow(BaseModel):
    geo_id: str = Field(description="cell_id (grid) or zip_code (zip).")
    centroid_lon: Optional[float] = None
    centroid_lat: Optional[float] = None
    median_ppsf: float
    avg_ppsf: float
    comp_count: int
    confidence_band: str = Field(description="'low' | 'med' | 'high'.")


class OfferRangeParams(BaseModel):
    """Recommended offer range (low/base/high) from comps by zip or cell."""
    living_sq_ft: float = Field(gt=0, description="Subject property living sqft.")
    zip_code: Optional[str] = Field(default=None)
    cell_id: Optional[int] = Field(default=None, description="0.25-mi grid cell; use when zip not provided.")
    sale_year: int = Field(default=2024, ge=2020)

    @root_validator(skip_on_failure=True)
    def require_zip_or_cell(cls, values):
        if values.get("zip_code") or values.get("cell_id") is not None:
            return values
        raise ValueError("Provide either zip_code or cell_id")


class OfferRangeRow(BaseModel):
    low_ppsf: float
    base_ppsf: float
    high_ppsf: float
    low_price: float
    base_price: float
    high_price: float
    comp_count: int
    geography_used: str = Field(description="'zip' | 'cell_025'.")


class OverpayRiskParams(BaseModel):
    """Overpay risk: list price vs comp-based value."""
    list_price: float = Field(gt=0)
    living_sq_ft: float = Field(gt=0)
    zip_code: Optional[str] = Field(default=None)
    cell_id: Optional[int] = Field(default=None)
    sale_year: int = Field(default=2024, ge=2020)

    @root_validator(skip_on_failure=True)
    def require_zip_or_cell(cls, values):
        if values.get("zip_code") or values.get("cell_id") is not None:
            return values
        raise ValueError("Provide either zip_code or cell_id")


class OverpayRiskRow(BaseModel):
    comp_median_ppsf: float
    comp_based_value: float
    list_price: float
    pct_above_comps: float = Field(description="Percent above comp-based value.")
    risk_level: str = Field(description="'low' | 'medium' | 'high'.")
    comp_count: int
    geography_used: str


class ConfidenceCoverageParams(BaseModel):
    """Confidence and coverage for a location (zip or cell)."""
    zip_code: Optional[str] = Field(default=None)
    cell_id: Optional[int] = Field(default=None)
    sale_year: int = Field(default=2024, ge=2020)

    @root_validator(skip_on_failure=True)
    def require_zip_or_cell(cls, values):
        if values.get("zip_code") or values.get("cell_id") is not None:
            return values
        raise ValueError("Provide either zip_code or cell_id")


class ConfidenceCoverageRow(BaseModel):
    geography_used: str = Field(description="'zip' | 'cell_025'.")
    geo_id: str
    comp_count: int
    confidence_band: str = Field(description="'low' | 'med' | 'high'.")
    effective_tier: Optional[int] = Field(default=None, description="1=0.25mi, 2=3x3, 3=5x5, 4=zip, 5=city.")
    effective_geometry_type: Optional[str] = Field(default=None)
    message: str = Field(description="Human-readable coverage warning or confirmation.")


# ---- Volume (for web visualizations: ZIP × year, city × year, ZIP × month) ----

class VolumeByZipYearParams(BaseModel):
    min_sold_date: date = Field(default=date(2020, 1, 1), description="Only sales on or after this date.")
    zip_code: Optional[str] = Field(default=None, description="Filter to one ZIP; null = all.")
    city_name: str = Field(default="LOS ANGELES", description="City filter (case-insensitive).")


class VolumeByZipYearRow(BaseModel):
    zip_code: str
    sale_year: int
    sale_count: int
    median_ppsf: Optional[float] = None
    median_dom: Optional[float] = None


class VolumeByCityYearParams(BaseModel):
    min_sold_date: date = Field(default=date(2020, 1, 1))
    city_name: str = Field(default="LOS ANGELES", description="City filter (case-insensitive).")


class VolumeByCityYearRow(BaseModel):
    city_id: Optional[int] = None
    city_name: str
    sale_year: int
    total_sales: int
    total_revenue: Optional[float] = None
    median_ppsf: Optional[float] = None
    avg_ppsf: Optional[float] = None


class VolumeByZipMonthParams(BaseModel):
    min_sold_date: date = Field(default=date(2020, 1, 1))
    zip_code: Optional[str] = Field(default=None)
    city_name: str = Field(default="LOS ANGELES", description="City filter (case-insensitive).")


class VolumeByZipMonthRow(BaseModel):
    zip_code: str
    sale_month: date
    sale_count: int
    median_ppsf: Optional[float] = None
    median_dom: Optional[float] = None


# ---- Rebuild decision system: feasibility (address workflow) ----

class FeasibilityCheckParams(BaseModel):
    """Input for parcel-level feasibility: what can we build here?"""
    property_id: int = Field(..., gt=0, description="Parcel (property_id) to check.")
    target_sqft: float = Field(..., gt=0, description="Target product size (e.g. 2700 sqft).")
    product_type: str = Field(
        default="SINGLE FAMILY RESIDENCE",
        description="Property subtype (e.g. SFR, duplex).",
    )
    city_name: Optional[str] = Field(default=None, description="City filter for comps; from property if not set.")
    lot_width_ft: Optional[float] = Field(default=None, gt=0, description="Override lot width (ft) when parcel data is missing.")
    lot_depth_ft: Optional[float] = Field(default=None, gt=0, description="Override lot depth (ft) when parcel data is missing.")


class FeasibilityCheckResult(BaseModel):
    """Result of feasibility check: pass/fail, reasons, recommended program, economics."""
    property_id: int
    target_sqft: float
    pass_fail: bool = Field(description="True = feasible for target product.")
    reason_codes: List[str] = Field(default_factory=list, description="Reason codes when fail (or empty when pass).")
    reason_messages: List[str] = Field(default_factory=list, description="Human-readable explanation for each reason code.")
    recommended_size_band_low: Optional[float] = Field(None, description="Recommended size band low (sqft).")
    recommended_size_band_high: Optional[float] = Field(None, description="Recommended size band high (sqft).")
    recommended_footprint_band: Optional[str] = Field(None, description="balanced | moderate | extreme.")
    max_gfa_estimate: Optional[float] = Field(None, description="Max buildable GFA from zoning (FAR × lot).")
    expected_p25_ppsf: Optional[float] = None
    expected_p50_ppsf: Optional[float] = None
    expected_p75_ppsf: Optional[float] = None
    expected_p25_price: Optional[float] = None
    expected_p50_price: Optional[float] = None
    expected_p75_price: Optional[float] = None
    expected_median_dom: Optional[float] = None
    expected_p75_dom: Optional[float] = None
    comp_count: int = 0
    confidence_band: Optional[str] = Field(None, description="low | med | high.")
    confidence_explanation: Optional[str] = None
    # Scenario outputs (cost model v0)
    scenario_base_margin_pct: Optional[float] = None
    scenario_downside_margin_pct: Optional[float] = None
    scenario_upside_margin_pct: Optional[float] = None
    scenario_base_irr: Optional[float] = None
    scenario_downside_irr: Optional[float] = None
    scenario_upside_irr: Optional[float] = None


# ---- Rebuild decision system: site search (parcel candidates) ----


class SiteSearchParams(BaseModel):
    """Find parcels where a target product could be built without starting from a specific property."""
    target_sqft: float = Field(..., gt=0, description="Target product size (e.g. 1500).")
    min_width_ft: Optional[float] = Field(default=None, gt=0, description="Minimum lot width (ft) to fit footprint.")
    min_depth_ft: Optional[float] = Field(default=None, gt=0, description="Minimum lot depth (ft) to fit footprint.")
    city_name: str = Field(default="LOS ANGELES", description="City filter (case-insensitive).")
    zip_code: Optional[str] = Field(default=None, description="Optional ZIP code filter.")
    zone_codes: Optional[List[str]] = Field(default=None, description="Optional list of acceptable zone codes.")
    limit: int = Field(default=100, ge=1, le=500, description="Max parcels to return.")
    # Target pipeline: older, smaller existing homes (e.g. 50 years old, ~1,400 sq ft).
    max_year_built: Optional[int] = Field(
        default=None,
        ge=1900,
        le=2030,
        description="Only parcels with building year_built <= this (e.g. 1975 for 50+ years old).",
    )
    min_living_sq_ft: Optional[float] = Field(
        default=None,
        gt=0,
        description="Only parcels whose current home size (latest sale living_sq_ft) >= this (e.g. 1200).",
    )
    max_living_sq_ft: Optional[float] = Field(
        default=None,
        gt=0,
        description="Only parcels whose current home size (latest sale living_sq_ft) <= this (e.g. 1600 for ~1,400).",
    )


class SiteSearchRow(BaseModel):
    """One candidate parcel that passes zoning + lot-size + footprint filters."""
    property_id: int
    zip_code: Optional[str] = None
    city_name: Optional[str] = None
    zone_code: Optional[str] = None
    lot_size_sq_ft: Optional[float] = None
    lot_width_ft: Optional[float] = None
    lot_depth_ft: Optional[float] = None
    max_gfa_estimate: Optional[float] = Field(None, description="Max buildable GFA from zoning (FAR × lot).")
    year_built: Optional[int] = Field(None, description="From latest sale when max_year_built / living_sq_ft filters used.")
    living_sq_ft: Optional[float] = Field(None, description="From latest sale when target-pipeline filters used.")


class TargetPipelineSummaryParams(BaseModel):
    """Same filters as site search; returns aggregate count and total value created (new-build value − existing)."""
    target_sqft: float = Field(..., gt=0, description="Target product size (e.g. 2700).")
    city_name: str = Field(default="LOS ANGELES", description="City filter.")
    zip_code: Optional[str] = Field(default=None, description="Optional ZIP filter.")
    max_year_built: Optional[int] = Field(default=None, ge=1900, le=2030, description="Only buildings year_built <= this (e.g. 1975).")
    min_living_sq_ft: Optional[float] = Field(default=None, gt=0, description="Only current home size >= this.")
    max_living_sq_ft: Optional[float] = Field(default=None, gt=0, description="Only current home size <= this.")
    zone_codes: Optional[List[str]] = Field(default=None, description="Optional zone filter.")
    limit: int = Field(default=5000, ge=1, le=10000, description="Max parcels to include in aggregate (cap).")


class TargetPipelineSummary(BaseModel):
    """Aggregate for target pipeline: count of qualifying parcels and total value created."""
    parcel_count: int = Field(description="Number of parcels where target fits and filters pass.")
    total_existing_value: Optional[float] = Field(None, description="Sum of existing value (latest sale) for parcels with sale.")
    total_new_build_value: Optional[float] = Field(None, description="Sum of (median new-build PPSF × target_sqft) by ZIP.")
    total_value_created: Optional[float] = Field(None, description="total_new_build_value − total_existing_value.")
    parcels_with_sale: int = Field(default=0, description="Parcels that had a sold_price in the aggregate.")
    zips_with_benchmark: int = Field(default=0, description="ZIPs that had new-build benchmark data.")


# ---- Rebuild decision system: product → where to build ----

class ProductWhereToBuildParams(BaseModel):
    """Input for ranking areas where a target product performs best."""
    target_sqft: float = Field(..., gt=0, description="Target product size (e.g. 2700).")
    product_type: str = Field(default="SINGLE FAMILY RESIDENCE", description="Property subtype.")
    city_name: str = Field(default="LOS ANGELES", description="City filter.")
    geography: str = Field(default="zip", description="'zip' or 'city' (submarket).")
    min_comp_count: int = Field(default=10, ge=0, description="Minimum comps for area to rank.")
    limit: int = Field(default=30, ge=1, le=200, description="Max areas to return.")


class AreaRankingRow(BaseModel):
    """One area (ZIP or city) in the product→where-to-build ranking."""
    geo_id: str = Field(description="ZIP code or city name.")
    geo_type: str = Field(description="'zip' | 'city'.")
    median_ppsf: Optional[float] = None
    median_dom: Optional[float] = None
    comp_count: int = 0
    confidence_band: Optional[str] = None
    supply_count: Optional[int] = Field(None, description="Parcels matching lot requirements.")
    score: Optional[float] = Field(None, description="Composite ranking score.")
    explanation: Optional[str] = None


# ---- Rebuild decision system: new-build benchmarking ----

class NewBuildBenchmarkParams(BaseModel):
    """Parameters for new-build benchmark. Comp set = new homes built since 2020 (last 5–6 years); new builds sell at a premium. No new builds in an area is a negative signal."""
    min_sold_date: str = Field(default="2020-01-01", description="Only sales on or after this date.")
    min_year_built: int = Field(default=2020, description="New-build cutoff: year_built >= this (since 2020 = last 5–6 years).")
    city_name: str = Field(default="LOS ANGELES")
    zip_code: Optional[str] = Field(default=None, description="Optional ZIP filter.")


class NewBuildBenchmarkRow(BaseModel):
    """One row: area + year with p25/p50/p75 PPSF and DOM for new builds."""
    zip_code: Optional[str] = None
    city_name: Optional[str] = None
    sale_year: int = 0
    sale_count: int = 0
    p25_ppsf: Optional[float] = None
    median_ppsf: Optional[float] = None
    p75_ppsf: Optional[float] = None
    p25_dom: Optional[float] = None
    median_dom: Optional[float] = None
    p75_dom: Optional[float] = None


# ---- Rebuild decision system: portfolio ranking ----

class PortfolioRankParams(BaseModel):
    """Input for portfolio/pipeline ranking."""
    property_ids: List[int] = Field(..., min_length=1, max_length=500, description="Parcel IDs to rank.")
    target_sqft: float = Field(..., gt=0)
    product_type: str = Field(default="SINGLE FAMILY RESIDENCE")


class PortfolioRankRow(BaseModel):
    """One parcel in portfolio rank: feasibility result summary + drivers."""
    property_id: int
    pass_fail: bool
    reason_codes: List[str] = Field(default_factory=list)
    expected_p50_price: Optional[float] = None
    scenario_base_margin_pct: Optional[float] = None
    comp_count: int = 0
    confidence_band: Optional[str] = None
    low_confidence_flag: bool = Field(default=False, description="True when comp_count low or confidence_band low.")

