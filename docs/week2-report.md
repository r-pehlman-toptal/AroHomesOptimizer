# Week 2 Report – LA Residential Design Optimization

**Project:** Aro Homes – LA Market Expansion (Data-Driven Design)  
**Period:** Week 2 of 8  
**Scope:** Canonical entities & gold schema + production serving layer (Postgres/PostGIS MVs, grid, refresh)  

---

## 1. Objectives (Week 2)

- Define and implement first gold views (`parcel_gold`, `transaction_gold`) and lock in backbone tables/keys.
- Add basic tests and a short data-quality memo.
- **Deliver the production-ready serving layer:** one-row-per-sale fact view, filtered LA fact MV, city×year and 0.25-mile grid×year aggregates, indexes for fast queries and `REFRESH CONCURRENTLY`, and a Python refresh script with documentation.

---

## 2. Completed Work

### 2.1 Gold Schema (canonical entities)

| Task | Status | Notes |
|------|--------|-------|
| Data map updated with chosen backbone tables/keys | [ ] | property_id, street_id, city_id, etc. |
| parcel_gold spec (columns + source table.column) | [ ] | e.g. `notes/parcel_gold_spec.md` |
| `sql/gold/parcel_gold.sql` implemented | [ ] | View or table; one row per parcel |
| `sql/gold/transaction_gold.sql` implemented | [ ] | One row per transaction; PPSF, DOM |
| Row-count / uniqueness tests | [ ] | `tests/test_row_counts.py` or similar |
| Data-quality memo (2–3 risks) | [ ] | Nulls, distributions, key risks |

### 2.2 Serving Layer (analytics schema)

| Task | Status | Deliverable |
|------|--------|-------------|
| Create `analytics` schema + PostGIS | Done | `sql/001_create_schema.sql` |
| Base clean view: one row per sale, no fan-out, LA | Done | `sql/010_v_fact_sale_clean.sql` |
| Filtered fact MV: sold_date ≥ 2020-01-01, ppsf ≥ 400 | Done | `sql/020_mv_sale_la_since2020_ppsf400.sql` |
| Indexes: UNIQUE(sale_id), (sale_year), (city_id, sale_year), (sold_date), GIST(point_3310) | Done | In 020 |
| City×year aggregate MV | Done | `sql/030_mv_agg_city_year_metrics.sql` |
| 0.25-mile grid table (402.336 m, EPSG:3310) | Done | `sql/040_grid_cells_025.sql` |
| Grid repopulate script (for refresh) | Done | `sql/041_populate_grid_cells_025.sql` |
| Grid×year PPSF MV (comp_count, median_ppsf, confidence_band) | Done | `sql/050_mv_agg_grid_year_ppsf_025.sql` |
| REFRESH CONCURRENTLY example | Done | `sql/090_refresh_concurrently.sql` |
| Python refresh script (order, --concurrently, --refresh-grid, timings) | Done | `scripts/refresh_mvs.py` |
| Serving-layer README (assumptions, indexes, cadence, Tableau) | Done | `docs/serving-layer-README.md` |

### 2.3 Verification

| Check | Status |
|-------|--------|
| Run migrations 001 → 010 → 020 → 030 → 040 → 050 in order | [ ] |
| `python scripts/refresh_mvs.py --concurrently true` completes | [ ] |
| Optional: `--refresh-grid` repopulates `analytics.grid_cells_025` | [ ] |
| Tableau or API can query `mv_agg_city_year_metrics` and `mv_agg_grid_year_ppsf_025` | [ ] |

---

## 3. Deliverables

1. **Gold:** parcel_gold and transaction_gold views/tables, spec, tests, data-quality memo.
2. **Serving layer:** SQL files `001`–`050`, `041`, `090`; `scripts/refresh_mvs.py`; `docs/serving-layer-README.md`.
3. **Week 2 report:** this document (with checkboxes filled and any blockers noted).

---

## 4. Blockers / Risks

- *Document any schema mismatches (e.g. missing `center_point` or `year_built`), LA boundary vs city-name filter, or refresh timing issues.*

---

## 5. Handoff to Week 3

- Gold views and data map feed feasibility and modeling.
- Serving-layer MVs are the source for Tableau dashboards and API aggregates; refresh cadence (e.g. nightly) should be scheduled.
- Week 3 focuses on zoning/feasibility foundations; grid and city×year metrics can be reused for submarket definitions.

---

*Update checkboxes and sections as work completes; save as `docs/week2-report.md`.*
