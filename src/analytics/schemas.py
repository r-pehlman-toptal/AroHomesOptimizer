from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from typing import Any, Dict, List, Optional


def _scope_default() -> str:
    return "county_wide"


@dataclass
class ScopeConfig:
    scope: str = _scope_default()  # 'county_wide' | 'target_markets'
    market_name: Optional[str] = None  # e.g. 'westside'
    counties: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    zips: Optional[List[str]] = None

    def to_json(self) -> Dict[str, Any]:
        return {
            "scope": self.scope,
            "market_name": self.market_name,
            "counties": self.counties,
            "cities": self.cities,
            "zips": self.zips,
        }


@dataclass
class LotHeatmapJobParams:
    scope: ScopeConfig
    geo_unit_type: str = "zip"  # 'zip' | 'city' | 'county'
    bucket_mode: str = "width_depth"  # or 'lot_size'
    width_bucket_ft: int = 5
    depth_bucket_ft: int = 5
    lot_size_bucket_sqft: int = 500

    def to_params_json(self) -> Dict[str, Any]:
        return {
            "geo_unit_type": self.geo_unit_type,
            "bucket_mode": self.bucket_mode,
            "width_bucket_ft": self.width_bucket_ft,
            "depth_bucket_ft": self.depth_bucket_ft,
            "lot_size_bucket_sqft": self.lot_size_bucket_sqft,
            "scope": self.scope.to_json(),
        }


@dataclass
class RegressionJobParams:
    scope: ScopeConfig
    date_range_start: date = date(2015, 1, 1)
    date_range_end: Optional[date] = None
    property_use: str = "SINGLE FAMILY RESIDENCE"
    min_ppsf: float = 100.0
    max_ppsf: float = 5000.0

    def to_params_json(self) -> Dict[str, Any]:
        base = asdict(self)
        base["scope"] = self.scope.to_json()
        return base


@dataclass
class ScenarioJobParams:
    regression_run_id: int
    size_min: int = 2000
    size_max: int = 3000
    size_step: int = 100

    def to_params_json(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValueMapJobParams:
    scope: ScopeConfig
    geo_unit_type: str = "zip"
    date_range_start: date = date(2015, 1, 1)
    date_range_end: Optional[date] = None
    property_use: str = "SINGLE FAMILY RESIDENCE"

    def to_params_json(self) -> Dict[str, Any]:
        base = asdict(self)
        base["scope"] = self.scope.to_json()
        return base

