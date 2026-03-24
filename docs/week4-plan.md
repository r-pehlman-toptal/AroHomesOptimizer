# Week 4 Plan – Aggregations and submarket lens

**Project:** Aro Homes – LA Market Expansion (Data-Driven Design)  
**Period:** Week 4 of 8  
**Scope:** Define LA submarkets; build/formalize aggregate views; exploratory analysis by submarket/typology; LA product archetypes.

---

## 1. Objectives

- **Define LA submarkets:** Choose canonical geography (city, neighborhood, macro/micro, or grid) and document in a list or config.
- **Implement or formalize aggregate views:** Ensure `city_year`, and either `submarket_year` or `grid_year`, with metrics (median/mean PPSF, DOM, volume) are queryable.
- **Exploratory analysis:** Use SQL + Python to compare distributions across submarkets and typologies (SFR vs small multifamily); produce 2–3 charts/tables.
- **LA product archetypes:** Propose 3–4 unit mixes/size bands to focus optimization on.
- **Coverage by geography:** Document “where we have enough comps” (tier 1–5) for dashboards.

---

## 2. Prerequisites (from Week 3)

- Feasibility module and zoning summary/nearby zoning APIs.
- Geometry coverage note and check script.
- **Serving layer:** `analytics.mv_agg_city_year_metrics`, `analytics.mv_agg_grid_year_ppsf_025`, `analytics.grid_cells_025`, `analytics.v_grid_year_effective_tier` (tier 1–5, effective_comp_count).
- **Gold:** `parcel_gold`, `transaction_gold`; `sql/agg/city_year.sql` (city × year with median_price_per_sqft, median_days_on_market from gold).

---

## 3. Tasks and deliverables

| Task | Deliverable |
|------|-------------|
| Define submarkets (city, neighborhood, or grid); choose canonical geography | **Submarket definition** (list or config, e.g. `docs/submarket-definition.md` or `data/submarkets.yaml`) |
| Implement or wire `sql/agg/city_year`, `submarket_year` (or grid_year) with PPSF, DOM, volume | **Working agg views** (city_year exists; add `submarket_year` if submarket ≠ city, or document grid as second geography and add `sql/agg/grid_year.sql` view over analytics MV if desired) |
| Compare distributions across submarkets and typologies (SFR vs small multifamily) | **Exploratory notebook or script** with 2–3 charts/tables |
| Propose 3–4 LA product archetypes (unit mixes/size bands) | **Archetype list** in report or `docs/la-product-archetypes.md` |
| Document “where we have enough comps” (tier 1–5) for dashboards | **Coverage by geography** (can reference `v_grid_year_effective_tier` and existing confidence_band) |
| Write Week 4 report | **Week 4 report** (e.g. `docs/week4-report.md`) |

---

## 4. Features (8) – Week 4 scope

| # | Feature | Notes |
|---|---------|--------|
| 1 | **DOM trend by area** | Grid×year or zip×year median DOM; leverage existing `volume_by_zip_year` (if DOM in response) or add query from gold/analytics. |
| 2 | **Seasonality (best months to buy)** | Volume and median price by month; already in API `volume_by_zip_month` and web UI. |
| 3 | **Resale liquidity proxy** | From comp_count and confidence_band (“homes here sell often” vs “thin market”); grid and comps-aggregate already expose this. |
| 4 | **New-build supply proxy** | Use `new_comp_count` (year_built ≥ 2019) in grid×year; already in `mv_agg_grid_year_ppsf_025`. |
| 5 | **Submarket PPSF comparison** | Compare median/avg PPSF across cities or custom submarkets; city_year and volume_by_city_year support this. |
| 6 | **Exploratory charts** | 2–3 distributions (e.g. PPSF by submarket, DOM by zip); deliver in notebook or script. |
| 7 | **LA product archetypes** | 3–4 unit mixes/size bands for optimization (per plan). |
| 8 | **Coverage by geography** | Document “where we have enough comps” (tier 1–5); use `v_grid_year_effective_tier` and confidence_band. |

---

## 5. Acceptance

- Submarket definition exists (list or config).
- Agg views (city_year and at least one of submarket_year / grid_year or documented use of analytics MVs) are queryable.
- One exploratory artifact (notebook or script) with 2–3 charts/tables.
- Archetype list (3–4) exists in report or dedicated doc.
- Week 4 report is written.

---

## 6. Handoff to Week 5

- Aggregates and submarket lens feed **feature tables** for baseline PPSF and DOM models (Week 5).
- Archetypes focus **optimization** on a small set of unit mixes/size bands.
- Coverage-by-geography informs which areas are safe for model application and dashboards.

---

## 7. References

- [docs/serving-layer-README.md](serving-layer-README.md) – analytics schema, city×year, grid×year, tier views.
- [docs/tableau/visualization_ladder.md](tableau/visualization_ladder.md) – data sources for city/grid.
- [sql/agg/city_year.sql](../sql/agg/city_year.sql) – existing city_year view.
- [scripts/refresh_mvs.py](../scripts/refresh_mvs.py) – MV refresh order.

---

*Update as work completes; save final state in `docs/week4-report.md`.*
