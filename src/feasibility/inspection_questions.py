"""
Inspection questions by year built (Week 3 feature).

Returns a list of suggested inspection questions based on parcel/MLS year_built.
Config: data/inspection_questions_by_year.yaml.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

# Project root: src/feasibility -> src -> root
_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG = _ROOT / "data" / "inspection_questions_by_year.yaml"

_LOADED: Optional[dict] = None


def _load_config() -> dict:
    global _LOADED
    if _LOADED is not None:
        return _LOADED
    if not _CONFIG.exists():
        _LOADED = {"bands": [], "default": {"questions": ["General condition?"]}}
        return _LOADED
    try:
        import yaml
        with open(_CONFIG, encoding="utf-8") as f:
            _LOADED = yaml.safe_load(f) or {}
    except Exception:
        _LOADED = {"bands": [], "default": {"questions": ["General condition?"]}}
    return _LOADED


def get_inspection_questions(year_built: Optional[int]) -> List[str]:
    """
    Return the list of inspection questions for the given year_built.

    Parameters
    ----------
    year_built : int or None
        From parcel_gold.year_built or MLS.

    Returns
    -------
    list of str
        Question text for UI. Uses default set when year_built is None or no band matches.
    """
    cfg = _load_config()
    bands = cfg.get("bands") or []
    default = cfg.get("default") or {}
    default_q = default.get("questions") or ["General condition?""]

    if year_built is None:
        return default_q

    for band in bands:
        min_y = band.get("min_year")
        max_y = band.get("max_year")
        if min_y is not None and year_built < min_y:
            continue
        if max_y is not None and year_built > max_y:
            continue
        qs = band.get("questions")
        if qs:
            return list(qs)

    return default_q


def get_inspection_band_label(year_built: Optional[int]) -> str:
    """Return the label for the band that applies (e.g. 'Pre-1960') or 'Unknown'."""
    cfg = _load_config()
    bands = cfg.get("bands") or []
    if year_built is None:
        return "Unknown"
    for band in bands:
        min_y = band.get("min_year")
        max_y = band.get("max_year")
        if min_y is not None and year_built < min_y:
            continue
        if max_y is not None and year_built > max_y:
            continue
        return band.get("label", "Unknown")
    return "Unknown"
