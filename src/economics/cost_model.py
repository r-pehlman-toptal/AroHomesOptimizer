"""
Rebuild decision system: cost model v0, profit/margin, IRR proxy, base/downside/upside scenarios.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CostModelParams:
    """Configurable cost assumptions."""
    hard_cost_per_sqft: float = 350.0
    soft_cost_pct: float = 0.15  # 15% of hard
    carry_cost_pct: float = 0.08  # 8% of (hard+soft) over hold period
    construction_months: float = 12.0
    marketing_months: float = 3.0  # assumed DOM


def compute_profit_margin(
    size_sqft: float,
    ppsf: float,
    params: Optional[CostModelParams] = None,
) -> tuple[float, float, float, float]:
    """
    Revenue = size_sqft * ppsf. Cost = hard + soft + carry. Returns (revenue, total_cost, profit, margin_pct).
    """
    p = params or CostModelParams()
    revenue = size_sqft * ppsf
    hard = size_sqft * p.hard_cost_per_sqft
    soft = hard * p.soft_cost_pct
    carry = (hard + soft) * p.carry_cost_pct
    total_cost = hard + soft + carry
    profit = revenue - total_cost
    margin_pct = (profit / revenue * 100.0) if revenue else 0.0
    return (revenue, total_cost, profit, margin_pct)


def irr_proxy(
    profit: float,
    total_cost: float,
    construction_months: float = 12.0,
    marketing_months: float = 3.0,
) -> float:
    """
    Simple IRR proxy: profit / total_cost / (years to exit). Years = (construction + marketing) / 12.
    """
    years = (construction_months + marketing_months) / 12.0
    if total_cost <= 0 or years <= 0:
        return 0.0
    return (profit / total_cost) / years  # rough annualized return


@dataclass
class ScenarioResult:
    """One scenario: base, downside, or upside."""
    label: str
    revenue: float
    total_cost: float
    profit: float
    margin_pct: float
    irr_proxy: float


def compute_scenarios(
    size_sqft: float,
    p50_ppsf: float,
    p25_ppsf: Optional[float] = None,
    p75_ppsf: Optional[float] = None,
    params: Optional[CostModelParams] = None,
) -> tuple[ScenarioResult, Optional[ScenarioResult], Optional[ScenarioResult]]:
    """
    Base (p50), downside (p25 or -10%), upside (p75 or +10%). Returns (base, downside, upside).
    """
    p = params or CostModelParams()
    base_rev, base_cost, base_profit, base_margin = compute_profit_margin(size_sqft, p50_ppsf, p)
    base_irr = irr_proxy(base_profit, base_cost, p.construction_months, p.marketing_months)
    base = ScenarioResult("base", base_rev, base_cost, base_profit, base_margin, base_irr)

    ppsf_down = p25_ppsf if p25_ppsf is not None else p50_ppsf * 0.9
    down_rev, down_cost, down_profit, down_margin = compute_profit_margin(size_sqft, ppsf_down, p)
    down_irr = irr_proxy(down_profit, down_cost, p.construction_months, p.marketing_months)
    downside = ScenarioResult("downside", down_rev, down_cost, down_profit, down_margin, down_irr)

    ppsf_up = p75_ppsf if p75_ppsf is not None else p50_ppsf * 1.1
    up_rev, up_cost, up_profit, up_margin = compute_profit_margin(size_sqft, ppsf_up, p)
    up_irr = irr_proxy(up_profit, up_cost, p.construction_months, p.marketing_months)
    upside = ScenarioResult("upside", up_rev, up_cost, up_profit, up_margin, up_irr)

    return (base, downside, upside)
