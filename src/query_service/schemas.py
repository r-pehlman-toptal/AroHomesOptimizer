from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, validator


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

