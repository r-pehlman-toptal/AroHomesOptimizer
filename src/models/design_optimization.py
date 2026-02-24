from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional

import cvxpy as cp
import numpy as np
import pandas as pd


@dataclass
class DesignOptimizationResult:
    unit_mix: Dict[str, float]
    total_gfa: float
    objective_value: float
    status: str


@dataclass
class SimpleEnvelopeOptimizer:
    """
    Sketch of a constraint‑based optimization model for a single site.

    The Principal DS is expected to:
    - Replace this with a richer formulation (NPV/IRR, cost layers, etc.).
    - Encode LA‑specific constraints from the feasibility layer.
    - Extend to multi‑site / portfolio‑level optimization as needed.
    """

    max_gfa: float  # max buildable gross floor area (from feasibility)
    unit_types: Dict[str, float]  # unit_type -> sqft per unit (e.g., { "1br": 650, ... })
    price_per_sqft: float  # can be parcel/submarket specific
    hard_constraints: Optional[Dict[str, Any]] = None

    def optimize(self) -> DesignOptimizationResult:
        unit_type_names = list(self.unit_types.keys())
        unit_sizes = np.array([self.unit_types[u] for u in unit_type_names])

        # Decision variables: count of each unit type
        x = cp.Variable(len(unit_type_names), nonneg=True)

        total_gfa = unit_sizes @ x
        revenue = self.price_per_sqft * total_gfa

        constraints = [
            total_gfa <= self.max_gfa,
        ]

        # Placeholder for additional constraint hooks
        # e.g., min share of family units, parking capacity, zoning overlays.
        if self.hard_constraints:
            # The DS can interpret and apply hard_constraints here.
            _ = self.hard_constraints

        problem = cp.Problem(cp.Maximize(revenue), constraints)
        problem.solve(solver=cp.ECOS, verbose=False)

        unit_mix = {name: float(val) for name, val in zip(unit_type_names, x.value)}
        return DesignOptimizationResult(
            unit_mix=unit_mix,
            total_gfa=float(total_gfa.value),
            objective_value=float(problem.value),
            status=problem.status,
        )

