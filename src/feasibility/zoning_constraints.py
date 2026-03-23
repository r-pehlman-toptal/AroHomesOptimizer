"""
Zoning constraint translation: parcel + zoning → model-ready constraints.

Builds max_gfa_estimate, max_height_ft, min_parking_spaces, max_units from
parcel gold, property_zoning + zone, and an optional zone-code lookup.
See docs/zoning-source-and-field-mapping.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd


# Default LA zone-code lookup (placeholder / typical values).
# Replace with staging_zoning or LAMC-derived table when available.
DEFAULT_LA_ZONE_LOOKUP = pd.DataFrame([
    {"zone_code": "R1", "max_far": 0.5, "max_height_ft": 30.0, "min_parking_spaces": 2.0, "max_units": 1},
    {"zone_code": "R2", "max_far": 0.5, "max_height_ft": 30.0, "min_parking_spaces": 2.0, "max_units": 2},
    {"zone_code": "RS", "max_far": 0.5, "max_height_ft": 30.0, "min_parking_spaces": 2.0, "max_units": 1},
    {"zone_code": "RE", "max_far": 0.35, "max_height_ft": 28.0, "min_parking_spaces": 2.0, "max_units": 1},
    {"zone_code": "RM", "max_far": 1.25, "max_height_ft": 45.0, "min_parking_spaces": 1.5, "max_units": 8},
])


@dataclass
class ZoningConstraintBuilder:
    """
    Translate parcel + zoning records into model-ready constraints.

    Joins parcels to zoning (one zone per parcel), then to a zone-code lookup
    (FAR, height, parking, units). Computes max_gfa_estimate = lot_size_sq_ft * max_far
    when both are present.
    """

    zone_lookup: Optional[pd.DataFrame] = None
    """
    Optional lookup: columns zone_code, max_far, max_height_ft, min_parking_spaces, max_units.
    If None, DEFAULT_LA_ZONE_LOOKUP is used.
    """

    def build_constraints(
        self,
        parcels: pd.DataFrame,
        zoning: pd.DataFrame,
        geom: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Build constraints table: one row per parcel with max_gfa_estimate,
        max_height_ft, min_parking_spaces, max_units.

        Parameters
        ----------
        parcels : DataFrame
            Must have parcel_id. Optional: lot_size_sq_ft (used for max_gfa_estimate).
        zoning : DataFrame
            Must have parcel_id and zone_code (or zone_name). One row per parcel
            (duplicates dropped by first occurrence).
        geom : DataFrame, optional
            If provided, merged on parcel_id. May contain lot_size_sq_ft if not in parcels.

        Returns
        -------
        DataFrame
            Parcel-level constraints with columns parcel_id, zone_code (if present),
            max_gfa_estimate, max_height_ft, min_parking_spaces, max_units, plus
            any columns from parcels (and geom) preserved.
        """
        lookup = self.zone_lookup if self.zone_lookup is not None else DEFAULT_LA_ZONE_LOOKUP

        # One zone per parcel
        zone_col = "zone_code" if "zone_code" in zoning.columns else "zone_name"
        if zone_col not in zoning.columns:
            raise ValueError("zoning must have 'zone_code' or 'zone_name'")
        zoning_one = zoning.drop_duplicates(subset=["parcel_id"], keep="first")[
            ["parcel_id", zone_col]
        ].rename(columns={zone_col: "zone_code"})

        df = parcels.merge(zoning_one, on="parcel_id", how="left")
        if geom is not None:
            geom_cols = [c for c in geom.columns if c != "parcel_id" and c not in df.columns]
            if geom_cols:
                df = df.merge(geom[["parcel_id"] + geom_cols], on="parcel_id", how="left")
            # Allow lot_size_sq_ft from geom to be used below
            if "lot_size_sq_ft" not in df.columns and "lot_size_sq_ft" in geom.columns:
                df = df.merge(geom[["parcel_id", "lot_size_sq_ft"]], on="parcel_id", how="left", suffixes=("", "_geom"))

        df = df.merge(lookup, on="zone_code", how="left")

        lot_sqft = df.get("lot_size_sq_ft")
        far = df.get("max_far")
        if lot_sqft is not None and far is not None:
            df["max_gfa_estimate"] = (lot_sqft * far).where(lot_sqft.notna() & far.notna(), pd.NA)
        else:
            df["max_gfa_estimate"] = pd.NA

        df["max_height_ft"] = df.get("max_height_ft", pd.Series(dtype=float))
        df["min_parking_spaces"] = df.get("min_parking_spaces", pd.Series(dtype=float))
        df["max_units"] = df.get("max_units", pd.Series(dtype=float))

        # Drop lookup-only columns if we duplicated names (keep only the constraint columns we want)
        for c in ["max_far"]:
            if c in df.columns and c != "max_gfa_estimate":
                df = df.drop(columns=[c], errors="ignore")

        return df


def summarize_constraints(
    constraints: pd.DataFrame,
    group_cols: Dict[str, Any],
) -> pd.DataFrame:
    """
    Summarize constraints at a submarket or zone level (e.g. median max_gfa by zone).
    """
    group_keys = list(group_cols) if isinstance(group_cols, dict) else group_cols
    agg_spec = {
        "max_gfa_estimate": "median",
        "max_height_ft": "median",
        "min_parking_spaces": "median",
        "max_units": "median",
    }
    existing = [c for c in agg_spec if c in constraints.columns]
    if not existing:
        return constraints.groupby(group_keys).size().reset_index(name="count")
    return constraints.groupby(group_keys).agg({c: "median" for c in existing}).reset_index()
