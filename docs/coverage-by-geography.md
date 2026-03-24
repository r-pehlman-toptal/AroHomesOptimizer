# Coverage by geography (Week 4)

**Purpose:** Document “where we have enough comps” for dashboards and model application. Coverage is expressed as **tiers 1–5**: from finest (0.25-mile cell) to fallback (city).

---

## 1. Tier definitions

| Tier | Geography | Description | Typical use |
|------|------------|-------------|-------------|
| 1 | **0.25-mile cell** | Single grid cell (~402 m). | Best for parcel-level inference when cell has ≥20 comps. |
| 2 | **3×3 cells** | ~0.75-mile neighborhood. | Fallback when tier 1 has &lt;20 comps. |
| 3 | **5×5 cells** | ~1.25-mile area. | Broader fallback. |
| 4 | **ZIP** | Primary ZIP (mode of sales in that cell). | ZIP-level comp count. |
| 5 | **City** | Primary city (mode of sales in that cell). | City-level comp count. |

**Minimum comp threshold:** 20 (configurable in the view definition). The first tier that has ≥20 comps is chosen as the “effective” geography for that cell × year.

---

## 2. Data sources

- **Comp counts per tier:** `analytics.v_grid_year_comp_tiers`  
  Columns: `cell_id`, `sale_year`, `comp_025`, `comp_3x3`, `comp_5x5`, `comp_zip`, `comp_city`, plus `primary_zip`, `primary_city_id`.

- **Effective tier and geography:** `analytics.v_grid_year_effective_tier`  
  Columns: same as above, plus:
  - `effective_tier` (1–5)
  - `effective_comp_count` (comp count at the chosen tier)
  - `effective_geometry_type` (`'cell_025' | 'cell_3x3' | 'cell_5x5' | 'zip' | 'city'`)

Use **`v_grid_year_effective_tier`** in dashboards to:
- Filter or color maps by “reliable” vs “thin” (e.g. effective_comp_count ≥ 20 and effective_tier ≤ 2).
- Choose which geography to use for PPSF or other inferences (e.g. use median_ppsf from grid when effective_tier = 1, or from ZIP/city when tier 4 or 5).

---

## 3. Confidence band (grid cell)

In **`analytics.mv_agg_grid_year_ppsf_025`** (and **`grid_year`** view), each cell × year has a **confidence_band**:

- `low`: comp_count &lt; 20  
- `med`: 20 ≤ comp_count &lt; 50  
- `high`: comp_count ≥ 50  

Use this for quick filtering in Tableau or the API (e.g. “show only high-confidence cells”) and for the resale liquidity proxy (“homes here sell often” vs “thin market”).

---

## 4. Dashboards and safe use

- **Maps:** Prefer coloring or filtering by `confidence_band` or `effective_tier` so users see where estimates are based on enough comps.
- **Model application:** When applying baseline PPSF/DOM models (Week 5), use `effective_geometry_type` and `effective_comp_count` to avoid applying cell-level estimates in thin cells; fall back to ZIP or city when tier &gt; 3.
- **Coverage by city:** For city-level submarkets, use `analytics.mv_agg_city_year_metrics` (total_sales, median_ppsf). No tier logic; cities with very few sales should be flagged in reporting.

---

## 5. References

- [docs/serving-layer-README.md](serving-layer-README.md) – tier views and Tableau usage.
- [sql/055_grid_year_tiers_fallback.sql](../sql/055_grid_year_tiers_fallback.sql) – definitions of `v_grid_year_comp_tiers` and `v_grid_year_effective_tier`.
- [docs/week4-plan.md](week4-plan.md) – Week 4 feature “Coverage by geography”.
