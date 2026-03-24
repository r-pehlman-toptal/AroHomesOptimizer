"""
Rebuild decision system: portfolio/pipeline ranking. Batch feasibility + economics, rank by margin/IRR.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.engine import Connection

from src.query_service.feasibility_engine import run_feasibility_check
from src.query_service.schemas import (
    FeasibilityCheckParams,
    FeasibilityCheckResult,
    PortfolioRankParams,
    PortfolioRankRow,
)


def portfolio_rank(conn: Connection, p: PortfolioRankParams) -> List[PortfolioRankRow]:
    """
    Run feasibility + economics for each parcel; return ranked list with reason codes and low-confidence flags.
    """
    rows: List[PortfolioRankRow] = []
    for pid in p.property_ids:
        params = FeasibilityCheckParams(
            property_id=pid,
            target_sqft=p.target_sqft,
            product_type=p.product_type,
        )
        res: FeasibilityCheckResult = run_feasibility_check(conn, params)
        low = (res.comp_count or 0) < 20 or (res.confidence_band or "").lower() == "low"
        rows.append(
            PortfolioRankRow(
                property_id=pid,
                pass_fail=res.pass_fail,
                reason_codes=res.reason_codes or [],
                expected_p50_price=res.expected_p50_price,
                scenario_base_margin_pct=res.scenario_base_margin_pct,
                comp_count=res.comp_count or 0,
                confidence_band=res.confidence_band,
                low_confidence_flag=low,
            )
        )
    # Rank: pass first, then by margin (desc), then by expected price (desc)
    rows.sort(
        key=lambda r: (
            not r.pass_fail,
            -(r.scenario_base_margin_pct or -999),
            -(r.expected_p50_price or 0),
        )
    )
    return rows
