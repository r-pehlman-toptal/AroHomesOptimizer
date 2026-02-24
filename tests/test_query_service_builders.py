from datetime import date

from src.query_service.schemas import (
    BedBathDistributionParams,
    PrincipalZoneParams,
    LotSizeBucketsParams,
    RankedZipsParams,
)


def test_bed_bath_params_defaults():
    p = BedBathDistributionParams()
    assert p.city == "LOS ANGELES"
    assert p.min_sold_date == date(2015, 1, 1)
    assert 2400 <= p.min_living_sqft < p.max_living_sqft
    assert 4 <= p.min_beds <= p.max_beds


def test_principal_zone_params_normalizes_cities():
    p = PrincipalZoneParams(cities=["los angeles", "pasadena"])
    assert p.cities == ["LOS ANGELES", "PASADENA"]


def test_lot_size_buckets_defaults():
    p = LotSizeBucketsParams()
    assert p.bucket_size_ft == 5
    assert p.zip_codes is None


def test_ranked_zips_params_defaults():
    p = RankedZipsParams()
    assert "LOS ANGELES" in p.allowed_counties
    assert "ORANGE" in p.allowed_counties
    assert p.min_ppsf < p.max_ppsf
    assert 0 < p.trim_lower_pct < p.trim_upper_pct < 1

