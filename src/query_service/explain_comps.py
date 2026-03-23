"""
Explainable comps: short text explaining why these comps were chosen ("why these comps").

Used by UI or API to display: same cell/zip, same year, similar size.
"""

from __future__ import annotations

from typing import Optional


def explain_comps_text(
    geography_used: str,
    sale_year: int,
    comp_count: int,
    zip_code: Optional[str] = None,
    living_sq_ft: Optional[float] = None,
) -> str:
    """
    Build a short explanation of why these comps were selected.

    Parameters
    ----------
    geography_used : str
        e.g. "zip" or "cell" (from F1/F3/F4 response).
    sale_year : int
        Sale year filter.
    comp_count : int
        Number of comps in the cohort.
    zip_code : str, optional
        ZIP when geography is zip-level.
    living_sq_ft : float, optional
        Subject living sq ft for "similar size" wording.

    Returns
    -------
    str
        One or two sentences for display in UI.
    """
    parts = []
    if geography_used and geography_used.lower() == "zip" and zip_code:
        parts.append(f"Same ZIP ({zip_code})")
    elif geography_used and (geography_used.lower() == "cell" or geography_used.lower() == "cell_025"):
        parts.append("Same 0.25-mile grid cell")
    else:
        parts.append("Same area")

    parts.append(f"same year ({sale_year})")
    if living_sq_ft is not None and living_sq_ft > 0:
        parts.append(f"similar size (subject {int(living_sq_ft):,} sq ft)")

    text = ", ".join(parts) + "."
    if comp_count > 0:
        text += f" {comp_count} comparable sale(s) in this cohort."
    return text
