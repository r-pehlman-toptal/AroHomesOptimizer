from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, root_validator, validator


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
    sale_year: int = Field(default=2024, ge=2020, description="Sale year filter.")
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

