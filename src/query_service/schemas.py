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


class F4OverpayRiskRow(BaseModel):
    comp_median_ppsf: float
    comp_based_value: float
    list_price: float
    pct_above_comps: float
    risk_level: str
    comp_count: int
    geography_used: str


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

