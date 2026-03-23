"""
Setback/height/FAR summary: format zoning constraints as short text for UI (Week 3 feature).

Source: ZoningConstraintBuilder output or POST /queries/zoning-summary response.
"""

from __future__ import annotations

from typing import Optional


def format_setback_height_far_summary(
    zone_code: Optional[str] = None,
    max_gfa_estimate: Optional[float] = None,
    max_height_ft: Optional[float] = None,
    min_parking_spaces: Optional[float] = None,
    max_units: Optional[int] = None,
    front_setback_ft: Optional[float] = None,
    side_setback_ft: Optional[float] = None,
    rear_setback_ft: Optional[float] = None,
) -> str:
    """
    Build a one- or two-line summary for display (e.g. "FAR 0.5, max height 30 ft, 2 parking. Setbacks: …").

    Omitted fields are not mentioned. Setbacks appear when any is provided.
    """
    parts = []
    if zone_code:
        parts.append(f"Zone {zone_code}.")
    if max_gfa_estimate is not None:
        parts.append(f"Max GFA ~{max_gfa_estimate:,.0f} sq ft")
    if max_height_ft is not None:
        parts.append(f"max height {max_height_ft:.0f} ft")
    if min_parking_spaces is not None:
        parts.append(f"{min_parking_spaces:.1f} parking min")
    if max_units is not None:
        parts.append(f"up to {max_units} unit(s)")

    line1 = ". ".join(parts) if parts else "No zoning constraints in lookup."

    setbacks = []
    if front_setback_ft is not None:
        setbacks.append(f"front {front_setback_ft:.0f} ft")
    if side_setback_ft is not None:
        setbacks.append(f"side {side_setback_ft:.0f} ft")
    if rear_setback_ft is not None:
        setbacks.append(f"rear {rear_setback_ft:.0f} ft")
    if setbacks:
        line1 += " Setbacks: " + ", ".join(setbacks) + "."

    return line1.strip()
