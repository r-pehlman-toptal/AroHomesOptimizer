"""
Rebuild decision system: reason-code taxonomy and explanation builder.
Maps reason codes + optional context to human-readable "why not?" / "why this?" messages.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.query_service.schemas import FEASIBILITY_REASON_CODES

# Human-readable messages for each reason code. Use {key} for optional context (e.g. lot_width_ft, required_width_ft).
REASON_MESSAGES: Dict[str, str] = {
    "width_too_narrow": "Lot width ({lot_width_ft:.0f} ft) is less than required ({required_width_ft:.0f} ft) for this product.",
    "depth_too_shallow": "Lot depth ({lot_depth_ft:.0f} ft) is less than required ({required_depth_ft:.0f} ft) for this product.",
    "insufficient_far": "Zoning or lot area does not support enough buildable GFA for this product.",
    "insufficient_comps": "Insufficient comparable sales to support a reliable price estimate.",
    "missing_geometry": "Parcel has no valid location (geometry) for proximity/comps.",
    "zoning_data_missing": "No zoning data found for this parcel.",
    "target_exceeds_max_gfa": "Target size ({target_sqft:.0f} sq ft) exceeds max buildable GFA ({max_gfa_estimate:.0f} sq ft).",
    "footprint_data_missing": "Lot width or depth is missing; cannot verify footprint fit.",
}


def build_reason_messages(
    reason_codes: List[str],
    context: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Map reason codes to human-readable sentences. Context can include lot_width_ft, required_width_ft,
    target_sqft, max_gfa_estimate, etc. for template substitution.
    """
    ctx = context or {}
    messages: List[str] = []
    for code in reason_codes:
        template = REASON_MESSAGES.get(code)
        if template:
            try:
                msg = template.format(**ctx)
            except (KeyError, ValueError):
                msg = code.replace("_", " ").title()
        else:
            msg = code.replace("_", " ").title()
        messages.append(msg)
    return messages
