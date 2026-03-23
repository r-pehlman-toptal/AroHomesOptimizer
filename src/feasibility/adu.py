"""
ADU feasibility check (Week 3 feature). Stub until LA ADU zoning rules are in DB/code.

When rules are defined (lot size, zone, setbacks, existing GFA, etc.), replace with
rule-based or lookup logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ADUFeasibilityResult:
    """Result of ADU feasibility check (stub or rule-based)."""
    status: str  # "stub" | "eligible" | "ineligible" | "unknown"
    message: str
    details: Optional[str] = None


def check_adu_feasibility(
    parcel_id: int,
    zone_code: Optional[str] = None,
    lot_size_sq_ft: Optional[float] = None,
) -> ADUFeasibilityResult:
    """
    Stub: LA ADU rules not yet in DB/code. Returns status and message for UI.

    When implemented: apply LA-specific ADU rules (zone, lot size, existing units, etc.)
    and return eligible / ineligible with details.
    """
    return ADUFeasibilityResult(
        status="stub",
        message="ADU feasibility requires LA zoning rules (lot size, zone, setbacks). Not yet implemented.",
        details="See docs/zoning-source-and-field-mapping.md. Add rules to this module or DB when available.",
    )
