from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import pandas as pd


@dataclass
class ZoningConstraintBuilder:
    """
    Translate parcel + zoning records into model‑ready constraints.

    Typical usage:
    - Load parcel, zoning, and geometry gold tables into DataFrames.
    - For each parcel (or candidate site), compute:
      - Max buildable GFA.
      - Envelope height, setbacks, and lot coverage.
      - Parking minimums, unit count caps, overlay rules.
    - Emit a tidy constraints table that can be joined into modeling pipelines.
    """

    def build_constraints(
        self,
        parcels: pd.DataFrame,
        zoning: pd.DataFrame,
        geom: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Placeholder implementation.

        The Principal DS will replace this with logic that reflects LA‑specific
        zoning rules and business conventions.
        """
        # Example: minimal join + stub fields to be expanded later
        df = (
            parcels.merge(zoning, on="parcel_id", how="left")
            .merge(geom, on="parcel_id", how="left")
        )

        # Stub: attach placeholder constraint columns to be filled with real logic
        df = df.copy()
        df["max_gfa_estimate"] = pd.NA
        df["max_height_ft"] = pd.NA
        df["min_parking_spaces"] = pd.NA
        df["max_units"] = pd.NA

        return df


def summarize_constraints(constraints: pd.DataFrame, group_cols: Dict[str, Any]) -> pd.DataFrame:
    """
    Example helper to summarize constraints at a submarket or zoning‑type level.

    This can support scenario analyses (e.g., typical max GFA by zone in a submarket).
    """
    group_keys = list(group_cols)
    agg_spec = {
        "max_gfa_estimate": "median",
        "max_height_ft": "median",
        "min_parking_spaces": "median",
        "max_units": "median",
    }
    return constraints.groupby(group_keys).agg(agg_spec).reset_index()

