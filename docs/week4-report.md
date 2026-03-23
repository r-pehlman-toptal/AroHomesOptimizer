# Week 4 report – Aggregations and submarket lens

**Focus:** Submarket definition (city + grid); aggregate views (city_year, grid_year); exploratory analysis (PPSF/DOM by city); LA product archetypes; coverage by geography.

---

## 1. Submarket definition

- **Doc:** [docs/submarket-definition.md](submarket-definition.md). **Config:** [data/submarkets.yaml](../data/submarkets.yaml) – canonical_geographies (city, grid_025mi) and cities list.
- **Canonical geographies:** (1) **City** – municipal boundary (city name); (2) **Grid** – 0.25-mile cell (EPSG:3310). City list for LA market: LOS ANGELES, BURBANK, GLENDALE, PASADENA, SANTA MONICA, LONG BEACH, INGLEWOOD, CULVER CITY, WEST HOLLYWOOD, SAN FERNANDO.
- **Sources:** City × year from `parcel_gold`/`transaction_gold` and `analytics.mv_agg_city_year_metrics`; grid × year from `analytics.mv_agg_grid_year_ppsf_025` and `analytics.grid_cells_025`. Typology (SFR vs small multifamily) is a dimension within city or grid.

**References:** [docs/week4-plan.md](week4-plan.md), [docs/serving-layer-README.md](serving-layer-README.md).

---

## 2. Aggregate views

- **city_year:** [sql/agg/city_year.sql](../sql/agg/city_year.sql) – city × year from gold: transaction_count, median_price_per_sqft, median_days_on_market, etc. Applied via `scripts/apply_gold.py` (optional).
- **grid_year:** [sql/agg/grid_year.sql](../sql/agg/grid_year.sql) – grid × year view over analytics: joins `analytics.mv_agg_grid_year_ppsf_025` and `analytics.grid_cells_025`; columns: cell_id, sale_year, comp_count, median_ppsf, avg_ppsf, new_comp_count, confidence_band, centroid_lat, centroid_lon. Requires analytics schema and MVs (run 030, 040, 041, 050 or `scripts/refresh_mvs.py`). Optional: applied by `scripts/apply_gold.py` (step 4; skips if analytics schema missing).

**References:** [docs/serving-layer-README.md](serving-layer-README.md), [scripts/refresh_mvs.py](../scripts/refresh_mvs.py).

---

## 3. Exploratory analysis

- **Script:** [scripts/explore_week4.py](../scripts/explore_week4.py)
- **Data:** Reads from `city_year` (gold) or, if missing, from `analytics.mv_agg_city_year_metrics`. Requires `DB_URL` and pandas.
- **Outputs:** (1) Summary table – latest year median PPSF and DOM by city (printed to stdout); (2) Chart – median PPSF by city over years (`scripts/out/week4_ppsf_by_city.png`); (3) Chart – median DOM by city over years (`scripts/out/week4_dom_by_city.png`) when DOM is available from city_year; (4) Chart – transaction volume by city over years (`scripts/out/week4_volume_by_city.png`). All charts require matplotlib.
- **Run:** `python scripts/explore_week4.py` from project root.

**References:** [docs/week4-plan.md](week4-plan.md) (Features: exploratory charts, submarket PPSF comparison).

---

## 4. LA product archetypes

- **Doc:** [docs/la-product-archetypes.md](la-product-archetypes.md)
- **Archetypes (4):** (1) SFR standard (1 unit, 1,200–2,800 sq ft; R1/RS/RE); (2) SFR plus ADU (1 + ADU; 300–1,200 sq ft ADU); (3) Small multifamily 2–4 units (600–1,400 sq ft/unit; R2/R3); (4) Multifamily 5–8 units (500–1,200 sq ft/unit; RM/R4). Used for optimization focus and Week 5 feature/model stratification.

**References:** [docs/week4-plan.md](week4-plan.md), [src/feasibility/zoning_constraints.py](../src/feasibility/zoning_constraints.py).

---

## 5. Coverage by geography

- **Doc:** [docs/coverage-by-geography.md](coverage-by-geography.md)
- **Tiers 1–5:** 0.25-mile cell → 3×3 → 5×5 → ZIP → city. Minimum 20 comps per tier; first tier with ≥20 comps is the “effective” geography for that cell × year.
- **Sources:** `analytics.v_grid_year_comp_tiers`, `analytics.v_grid_year_effective_tier` (effective_tier, effective_comp_count, effective_geometry_type). Grid cell confidence_band (low/med/high) in `mv_agg_grid_year_ppsf_025` / `grid_year`.

**References:** [docs/serving-layer-README.md](serving-layer-README.md), [sql/055_grid_year_tiers_fallback.sql](../sql/055_grid_year_tiers_fallback.sql).

---

## 6. Week 4 features (8)

| # | Feature | Status |
|---|---------|--------|
| 1 | DOM trend by area | Supported by city_year (median_days_on_market) and explore script; grid×year DOM can be added from fact if needed. |
| 2 | Seasonality (best months to buy) | API `volume_by_zip_month` and web UI. |
| 3 | Resale liquidity proxy | comp_count and confidence_band in grid_year and comps-aggregate. |
| 4 | New-build supply proxy | new_comp_count in mv_agg_grid_year_ppsf_025 / grid_year. |
| 5 | Submarket PPSF comparison | volume_by_city_year, city_year, explore_week4.py. |
| 6 | Exploratory charts | scripts/explore_week4.py (summary table + PPSF, DOM, volume by city). |
| 7 | LA product archetypes | docs/la-product-archetypes.md (4 archetypes). |
| 8 | Coverage by geography | docs/coverage-by-geography.md and v_grid_year_effective_tier. |

---

## 7. Week 4 completion summary

Week 4 is complete. Delivered: **(1) submarket definition** – [docs/submarket-definition.md](submarket-definition.md) and [data/submarkets.yaml](../data/submarkets.yaml) (city + grid, city list, typology note); **(2) agg views** – city_year (existing), [sql/agg/grid_year.sql](../sql/agg/grid_year.sql) over analytics MV, optionally applied by [scripts/apply_gold.py](../scripts/apply_gold.py); **(3) exploratory artifact** – [scripts/explore_week4.py](../scripts/explore_week4.py) with summary table and 3 charts (PPSF, DOM, volume by city); **(4) LA product archetypes** – [docs/la-product-archetypes.md](la-product-archetypes.md) (4 unit mixes/size bands); **(5) coverage by geography** – [docs/coverage-by-geography.md](coverage-by-geography.md) (tiers 1–5, effective_tier, confidence_band). All eight Week 4 features are addressed. Handoff to Week 5: aggregates and submarket lens feed feature tables and baseline PPSF/DOM models; archetypes focus optimization; coverage informs safe use of models and dashboards.
