"""
Confidence score and band from four comp aggregate signals.

Signals (each 0–1):
  • coverage:   min(1, comp_count / 30)
  • proximity:  exp(-median_distance / 0.5)
  • recency:    exp(-median_months_ago / 6)
  • tightness:  1 - min(1, iqr_ppsf / median_ppsf)

Example: confidence = 0.35*coverage + 0.25*proximity + 0.25*recency + 0.15*tightness

Bands: >= 0.75 high, >= 0.55 med, else low.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple


def confidence_components(
    comp_count: int,
    median_ppsf: Optional[float],
    iqr_ppsf: Optional[float],
    median_dist_miles: Optional[float],
    median_months_ago: Optional[float],
    coverage_target: int = 30,
    proximity_halflife_miles: float = 0.5,
    recency_halflife_months: float = 6.0,
) -> Tuple[float, float, float, float]:
    """Return (coverage, proximity, recency, tightness) each in [0, 1]."""
    coverage = min(1.0, comp_count / coverage_target) if comp_count >= 0 else 0.0
    proximity = math.exp(-median_dist_miles / proximity_halflife_miles) if median_dist_miles is not None and median_dist_miles >= 0 else 0.0
    recency = math.exp(-median_months_ago / recency_halflife_months) if median_months_ago is not None and median_months_ago >= 0 else 0.0
    if median_ppsf is not None and median_ppsf > 0 and iqr_ppsf is not None and iqr_ppsf >= 0:
        tightness = 1.0 - min(1.0, iqr_ppsf / median_ppsf)
    else:
        tightness = 0.0
    return round(coverage, 4), round(proximity, 4), round(recency, 4), round(tightness, 4)


def confidence_score_and_band(
    comp_count: int,
    median_ppsf: Optional[float],
    iqr_ppsf: Optional[float],
    median_dist_miles: Optional[float],
    median_months_ago: Optional[float],
    coverage_target: int = 30,
    proximity_halflife_miles: float = 0.5,
    recency_halflife_months: float = 6.0,
    weights: Optional[Tuple[float, float, float, float]] = None,
) -> Tuple[float, str]:
    """
    Compute confidence score (0–1) and band ('low' | 'med' | 'high') from aggregate row.

    Four signals: coverage, proximity, recency, tightness (see module docstring).
    Weights default: (0.35 coverage, 0.25 proximity, 0.25 recency, 0.15 tightness).
    """
    if weights is None:
        weights = (0.35, 0.25, 0.25, 0.15)
    w_cov, w_prox, w_rec, w_tight = weights

    coverage, proximity, recency, tightness = confidence_components(
        comp_count, median_ppsf, iqr_ppsf, median_dist_miles, median_months_ago,
        coverage_target, proximity_halflife_miles, recency_halflife_months,
    )

    score = w_cov * coverage + w_prox * proximity + w_rec * recency + w_tight * tightness
    score = max(0.0, min(1.0, score))

    if score >= 0.75:
        band = "high"
    elif score >= 0.55:
        band = "med"
    else:
        band = "low"

    return round(score, 4), band
