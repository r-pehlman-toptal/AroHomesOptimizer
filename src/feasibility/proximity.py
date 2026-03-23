"""
Proximity to essentials: distance from parcel center_point to POI (groceries, hospitals, parks).

Data: parcel_gold.center_point_4326 (or parcel_center_point SQL). External POI not in DB;
caller provides POI list or uses external API. This module provides a pure distance helper
and a stub for "nearest POI" when POI data is supplied.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple


def distance_km(lon_lat: Tuple[float, float], poi_lon_lat: Tuple[float, float]) -> float:
    """
    Approximate distance in km between two (lon, lat) points (Haversine).
    """
    lon1, lat1 = lon_lat
    lon2, lat2 = poi_lon_lat
    R = 6371.0  # Earth radius km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def distances_to_pois(
    parcel_lon_lat: Tuple[float, float],
    pois: List[Tuple[str, float, float]],
) -> List[Tuple[str, float]]:
    """
    Return list of (poi_label, distance_km) for each POI.
    pois: list of (label, longitude, latitude).
    """
    return [
        (label, round(distance_km(parcel_lon_lat, (lon, lat)), 3))
        for label, lon, lat in pois
    ]


def nearest_poi_stub(
    parcel_id: int,
    poi_type: str,
) -> str:
    """
    Stub: external POI data not in DB. Returns message for UI.
    When POI layer or API is available, replace with real lookup using parcel center_point.
    """
    return (
        "Proximity to essentials (e.g. groceries, hospitals, parks) requires external POI data. "
        "Use POST /queries/parcel-center to get parcel coordinates, then compute distances in app or via external API."
    )
