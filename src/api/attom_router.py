"""Attom-backed property details: proxy so API key stays server-side."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from typing import List as TypingList

from src.api.dependencies import cognito_auth_dependency
from src.attom.client import (
    fetch_property_detail,
    fetch_avm_in_radius,
    fetch_sale_history,
    fetch_rebuild_features,
    fetch_new_build_benchmark_attom,
    fetch_new_build_properties_for_map,
    fetch_target_sites_attom,
    fetch_product_mix_attom,
    fetch_value_accretion_heatmap_attom,
)


router = APIRouter(
    prefix="/attom",
    tags=["attom"],
    dependencies=[Depends(cognito_auth_dependency)],
)


class AttomPropertyDetailsRequest(BaseModel):
    address: str = Field(..., min_length=5, description="Full address, e.g. 11401 Clover Ave, Los Angeles, CA 90066")


class AttomAvmInRadiusRequest(BaseModel):
    address: str = Field(..., min_length=5, description="Center address for radius search")
    radius_miles: float = Field(0.1, ge=0.05, le=10.0, description="Radius in miles (0.05–10)")


@router.post("/property-details")
def api_attom_property_details(params: AttomPropertyDetailsRequest) -> dict:
    """
    Look up property details from Attom by address. Returns Zillow-style fields:
    full_address, beds, baths, living_sq_ft, lot_sq_ft, year_built, property_type,
    last_sale_amount, last_sale_date, avm_value, etc. Sale history is omitted so the
    UI can load it asynchronously via POST /attom/sale-history.
    """
    result = fetch_property_detail(params.address.strip())
    if result.get("property") is not None:
        result["property"]["sale_history"] = []
    return result


class AttomSaleHistoryRequest(BaseModel):
    address: str = Field(..., min_length=5, description="Full address (same as property-details)")


class AttomRebuildFeaturesRequest(BaseModel):
    address: str = Field(..., min_length=5, description="Full address for property lookup")
    target_living_sq_ft: Optional[float] = Field(None, gt=0, description="Optional target sqft; when set, gap_to_target_sqft is calculated.")


class AttomRebuildFeatures(BaseModel):
    """Rebuild-oriented features from Attom; includes DB-aligned fields (PropertyInfoRow / ParcelFootprintRow names)."""
    full_address: Optional[str] = None
    # Value (from API)
    avm_value: Optional[float] = None
    avm_high: Optional[float] = None
    avm_low: Optional[float] = None
    avm_confidence: Optional[float] = None
    avm_per_sqft: Optional[float] = None
    last_sale_amount: Optional[float] = None
    last_sale_date: Optional[str] = None
    assessed_value: Optional[float] = None
    tax_amount: Optional[float] = None
    tax_year: Optional[float] = None
    market_value: Optional[float] = None
    # Calculated
    suggested_existing_value: Optional[float] = None
    suggested_existing_value_source: Optional[str] = None  # "avm" | "last_sale" | "sale_history"
    value_per_sqft: Optional[float] = None
    gap_to_target_sqft: Optional[float] = None
    # Improvement (from API)
    year_built: Optional[int] = None
    living_sq_ft: Optional[float] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    property_type: Optional[str] = None
    # Lot (from API)
    lot_sq_ft: Optional[float] = None
    # Id / geocoding (from API)
    attom_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sale_count: int = 0
    # ---- DB-aligned (same names as PropertyInfoRow) ----
    sold_date: Optional[str] = None
    sold_price: Optional[float] = None
    ppsf: Optional[float] = None
    property_use_standardized: Optional[str] = None
    zip_code: Optional[str] = None
    city_name: Optional[str] = None
    days_on_market: Optional[float] = None
    # ---- DB-aligned (same names as ParcelFootprintRow) ----
    lot_size_sq_ft: Optional[float] = None
    lot_width_ft: Optional[float] = None
    lot_depth_ft: Optional[float] = None
    ratio_band: Optional[str] = None
    is_valid_dimensions: bool = False
    footprint_notes: Optional[str] = None
    # ---- Estimated buildable (calculated from lot area + assumed setbacks when no zoning) ----
    buildable_width_ft: Optional[float] = None
    buildable_depth_ft: Optional[float] = None
    buildable_sq_ft: Optional[float] = None
    buildable_notes: Optional[str] = None
    fits_target_sqft: Optional[bool] = None  # True if buildable_sq_ft >= target_living_sq_ft when target given

    model_config = {"extra": "allow"}  # allow client to add fields without breaking response

    @field_validator("attom_id", mode="before")
    @classmethod
    def attom_id_to_str(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, (int, float)):
            return str(int(v))
        return str(v)


@router.post("/rebuild-features")
def api_attom_rebuild_features(params: AttomRebuildFeaturesRequest) -> dict:
    """
    Rebuild-oriented features from Attom (Phase 1: Attom only). Uses property/detail API;
    when the API doesn't provide a value we calculate it (e.g. suggested_existing_value,
    value_per_sqft, gap_to_target_sqft when target_living_sq_ft given).
    """
    result = fetch_rebuild_features(params.address.strip(), params.target_living_sq_ft)
    if result.get("rebuild_features") is not None:
        result["rebuild_features"] = AttomRebuildFeatures.model_validate(result["rebuild_features"]).model_dump()
    return result


@router.post("/sale-history")
def api_attom_sale_history(params: AttomSaleHistoryRequest) -> dict:
    """
    Fetch only sale history for an address. Call this asynchronously after
    property-details so the main card appears first and price history loads when ready.
    """
    return fetch_sale_history(params.address.strip())


class AttomNewBuildBenchmarkRequest(BaseModel):
    zip_code: str = Field(..., min_length=5, description="ZIP code to search for new-build sales")
    min_year_built: int = Field(2020, ge=2000, le=2030, description="Only include homes built on or after this year (default 2020 = last 5–6 years)")
    page_size: int = Field(100, ge=1, le=200, description="Max records to fetch from Attom (1–200)")


class AttomNewBuildBenchmarkResponse(BaseModel):
    error: Optional[str] = None
    zip_code: str
    min_year_built: int
    sale_count: int
    p25_ppsf: Optional[float] = None
    median_ppsf: Optional[float] = None
    p75_ppsf: Optional[float] = None
    p25_dom: Optional[float] = None
    median_dom: Optional[float] = None
    p75_dom: Optional[float] = None
    has_new_builds: bool
    note: str


@router.post("/new-build-benchmark", response_model=AttomNewBuildBenchmarkResponse)
def api_attom_new_build_benchmark(params: AttomNewBuildBenchmarkRequest) -> AttomNewBuildBenchmarkResponse:
    """
    New-build benchmark (PPSF + DOM) for a ZIP code, using Attom sale data.
    Comp set = homes with year_built >= min_year_built (default 2020).
    Returns p25/p50/p75 PPSF and days-on-market.
    has_new_builds = False is a negative signal for the area.
    """
    result = fetch_new_build_benchmark_attom(
        zip_code=params.zip_code,
        min_year_built=params.min_year_built,
        page_size=params.page_size,
    )
    return AttomNewBuildBenchmarkResponse(
        error=result.get("error"),
        zip_code=result.get("zip_code", params.zip_code),
        min_year_built=result.get("min_year_built", params.min_year_built),
        sale_count=result.get("sale_count", 0),
        p25_ppsf=result.get("p25_ppsf"),
        median_ppsf=result.get("median_ppsf"),
        p75_ppsf=result.get("p75_ppsf"),
        p25_dom=result.get("p25_dom"),
        median_dom=result.get("median_dom"),
        p75_dom=result.get("p75_dom"),
        has_new_builds=result.get("has_new_builds", False),
        note=result.get("note", ""),
    )


class AttomNewBuildMapRequest(BaseModel):
    zip_code: Optional[str] = Field(None, description="ZIP code filter. Leave blank to search the whole LA area by radius.")
    min_year_built: int = Field(2020, ge=2000, le=2030, description="Only homes built on or after this year (default 2020)")
    page_size: int = Field(100, ge=1, le=200, description="Max records to fetch (1–200)")
    latitude: Optional[float] = Field(None, description="Center lat for radius search (used when zip_code is blank)")
    longitude: Optional[float] = Field(None, description="Center lon for radius search (used when zip_code is blank)")
    radius_miles: Optional[float] = Field(None, ge=0.5, le=50.0, description="Radius in miles when using lat/lon (default 20 mi)")


@router.post("/new-build-map")
def api_attom_new_build_map(params: AttomNewBuildMapRequest) -> dict:
    """
    Per-property new-build sale data for geographic map plotting.
    - With zip_code: filters by ZIP.
    - Without zip_code: uses lat/lon + radius (defaults to LA center, 20-mile radius).
    Returns list of properties with lat, lon, living_sq_ft, lot_sq_ft,
    year_built, sale_amt, ppsf. Color map by home size or lot size in UI.
    """
    return fetch_new_build_properties_for_map(
        zip_code=params.zip_code,
        min_year_built=params.min_year_built,
        page_size=params.page_size,
        latitude=params.latitude,
        longitude=params.longitude,
        radius_miles=params.radius_miles,
    )


class AttomTargetSitesRequest(BaseModel):
    zip_code: Optional[str] = Field(None, description="ZIP code filter. Blank = LA area by radius.")
    latitude: Optional[float] = Field(None, description="Center lat (used when zip_code is blank)")
    longitude: Optional[float] = Field(None, description="Center lon (used when zip_code is blank)")
    radius_miles: float = Field(20.0, ge=0.5, le=50.0, description="Radius in miles when no ZIP (default 20)")
    max_year_built: int = Field(1975, ge=1900, le=2010, description="Homes built on or before this year (~50 yr old = 1975)")
    min_living_sq_ft: int = Field(1100, ge=200, le=5000, description="Min living sqft (default 1100)")
    max_living_sq_ft: int = Field(1700, ge=200, le=5000, description="Max living sqft (default 1700)")
    target_build_sq_ft: float = Field(2700.0, ge=500, le=8000, description="Target new home sqft to test for feasibility")
    front_setback_ft: float = Field(20.0, ge=0, le=100, description="Front yard setback in feet (default 20)")
    rear_setback_ft: float = Field(20.0, ge=0, le=100, description="Rear yard setback in feet (default 20)")
    side_setback_ft: float = Field(5.0, ge=0, le=50, description="Side yard setback in feet (default 5, applied to each side)")
    page_size: int = Field(100, ge=1, le=500, description="Max records to fetch (1–500; Attom paginates at 200/page)")


@router.post("/target-sites")
def api_attom_target_sites(params: AttomTargetSitesRequest) -> dict:
    """
    Find density/incidence of ~50-yr-old, ~1,400 sqft homes on buildable lots.
    Uses Attom /property/snapshot + maxYearBuilt + living sqft range.
    Returns total count, buildable %, lot-width distribution, p25/p50/p75 dimensions,
    and per-property list for map plotting.
    """
    return fetch_target_sites_attom(
        zip_code=params.zip_code,
        latitude=params.latitude,
        longitude=params.longitude,
        radius_miles=params.radius_miles,
        max_year_built=params.max_year_built,
        min_living_sq_ft=params.min_living_sq_ft,
        max_living_sq_ft=params.max_living_sq_ft,
        target_build_sq_ft=params.target_build_sq_ft,
        front_setback_ft=params.front_setback_ft,
        rear_setback_ft=params.rear_setback_ft,
        side_setback_ft=params.side_setback_ft,
        page_size=params.page_size,
    )


class AttomProductMixRequest(BaseModel):
    zip_code: Optional[str] = Field(None, description="ZIP code filter. Blank = LA area by radius.")
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)
    radius_miles: float = Field(20.0, ge=0.5, le=50.0)
    max_year_built: int = Field(1975, ge=1900, le=2010, description="Existing homes built on or before this year")
    min_living_sq_ft: int = Field(1100, ge=200, le=5000)
    max_living_sq_ft: int = Field(1700, ge=200, le=5000)
    target_sizes: TypingList[int] = Field(
        default=[2100, 2400, 2700, 3000, 3500],
        description="List of target build sqft to sweep (e.g. [2100, 2700, 3500])",
    )
    front_setback_ft: float = Field(20.0, ge=0, le=100)
    rear_setback_ft: float = Field(20.0, ge=0, le=100)
    side_setback_ft: float = Field(5.0, ge=0, le=50)
    benchmark_zip_code: Optional[str] = Field(None, description="ZIP for new-build PPSF benchmark (defaults to zip_code)")
    min_year_built_comps: int = Field(2020, ge=2000, le=2030, description="New-build comp cutoff year (default 2020)")
    page_size: int = Field(200, ge=1, le=500, description="Max records (1–500; Attom paginates at 200/page)")


@router.post("/product-mix")
def api_attom_product_mix(params: AttomProductMixRequest) -> dict:
    """
    Product mix optimizer: find the target home size that maximises
    quantity × value creation across the area.
    Fetches all target sites once, sweeps target_sizes in-memory,
    returns per-size buildable count + value accretion + total value created.
    """
    return fetch_product_mix_attom(
        zip_code=params.zip_code,
        latitude=params.latitude,
        longitude=params.longitude,
        radius_miles=params.radius_miles,
        max_year_built=params.max_year_built,
        min_living_sq_ft=params.min_living_sq_ft,
        max_living_sq_ft=params.max_living_sq_ft,
        target_sizes=params.target_sizes,
        front_setback_ft=params.front_setback_ft,
        rear_setback_ft=params.rear_setback_ft,
        side_setback_ft=params.side_setback_ft,
        benchmark_zip_code=params.benchmark_zip_code,
        min_year_built_comps=params.min_year_built_comps,
        page_size=params.page_size,
    )


class AttomValueAccretionMapRequest(BaseModel):
    zip_code: Optional[str] = Field(None, description="ZIP code filter. Blank = LA area by radius.")
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)
    radius_miles: float = Field(20.0, ge=0.5, le=50.0)
    max_year_built: int = Field(1975, ge=1900, le=2010)
    min_living_sq_ft: int = Field(1100, ge=200, le=5000)
    max_living_sq_ft: int = Field(1700, ge=200, le=5000)
    target_build_sq_ft: float = Field(2700.0, ge=500, le=8000, description="Single target home size (sqft)")
    front_setback_ft: float = Field(20.0, ge=0, le=100)
    rear_setback_ft: float = Field(20.0, ge=0, le=100)
    side_setback_ft: float = Field(5.0, ge=0, le=50)
    min_year_built_comps: int = Field(2020, ge=2000, le=2030)
    page_size: int = Field(200, ge=1, le=500)


@router.post("/value-accretion-map")
def api_attom_value_accretion_map(params: AttomValueAccretionMapRequest) -> dict:
    """
    Value accretion heat map for a single target home size.
    PPSF is fetched once per ZIP (parallel), applied to all properties in that ZIP.
    Returns per-property value_accretion = (zip_ppsf × target_sqft) − existing_value,
    plus per-ZIP PPSF baseline table for the heat map layer.
    """
    return fetch_value_accretion_heatmap_attom(
        zip_code=params.zip_code,
        latitude=params.latitude,
        longitude=params.longitude,
        radius_miles=params.radius_miles,
        max_year_built=params.max_year_built,
        min_living_sq_ft=params.min_living_sq_ft,
        max_living_sq_ft=params.max_living_sq_ft,
        target_build_sq_ft=params.target_build_sq_ft,
        front_setback_ft=params.front_setback_ft,
        rear_setback_ft=params.rear_setback_ft,
        side_setback_ft=params.side_setback_ft,
        min_year_built_comps=params.min_year_built_comps,
        page_size=params.page_size,
    )


@router.post("/avm-in-radius")
def api_attom_avm_in_radius(params: AttomAvmInRadiusRequest) -> dict:
    """
    Estimated value of properties within a given radius of an address.
    Geocodes the address, then calls Attom AVM snapshot and returns aggregate
    (property_count, median_avm_value, mean_avm_value, min/max) plus optional list of properties.
    """
    return fetch_avm_in_radius(params.address.strip(), params.radius_miles)
