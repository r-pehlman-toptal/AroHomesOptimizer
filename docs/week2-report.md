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
| Data map updated with chosen backbone tables/keys | Done | `docs/data-map.md` – property_id, street_id, city_id, join paths |
| parcel_gold spec (columns + source table.column) | Done | `notes/parcel_gold_spec.md` |
| `sql/gold/parcel_gold.sql` implemented | Done | View; one row per parcel (property_address → street → city, geometry, year_built) |
| `sql/gold/transaction_gold.sql` implemented | Done | View; one row per mls_history.id; parcel_id, close_date, price_per_sqft, days_on_market |
| Row-count / uniqueness tests | Done | `tests/test_row_counts.py` – parcel/transaction uniqueness + FK check |
| Data-quality memo (2–3 risks) | Done | `notes/data-quality-memo.md` – nulls, referential consistency, outliers |

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

### 2.3 Read-only Query Service (F1, F3, F4)

For environments with **read-only** DB access (no CREATE schema/view/MV/COMMENT), parameterized SQL and FastAPI endpoints use **public tables only**.

**F1 Comps** — `POST /queries/f1/comps`  
Returns comparable sales for a given ZIP and year. **Parameters:** `zip_code` (required), `sale_year` (default 2024), `limit` (default 10, max 50), `min_comps` (default 30, for UI low-sample warning), `ppsf_min` (default 400). **Response:** one row per comp with `sale_id`, `property_id`, `sold_date`, `sold_price`, `living_sq_ft`, `ppsf`, `zip_code`, `city_name`, `year_built`, `comp_count`, `confidence_band`. Use `comp_count` and `confidence_band` from the first row for a confidence summary in the UI.

**F3 Offer range** — `POST /queries/f3/offer-range`  
Returns low/base/high PPSF and price for a subject size in a ZIP. **Parameters:** `zip_code`, `living_sq_ft`, `sale_year` (default 2024), `ppsf_min` (default 400). **Response:** one row with `low_ppsf`, `base_ppsf`, `high_ppsf`, `low_price`, `base_price`, `high_price`, `comp_count`, `geography_used`. Percentiles are p25/p50/p75 for that ZIP × year; prices are those percentiles × `living_sq_ft`. Empty if no comps.

**F4 Overpay risk** — `POST /queries/f4/overpay-risk`  
Compares list price to comp-based value and returns overpay risk. **Parameters:** `zip_code`, `list_price`, `living_sq_ft`, `sale_year` (default 2024), `ppsf_min` (default 400). **Response:** one row with `comp_median_ppsf`, `comp_based_value`, `list_price`, `pct_above_comps`, `risk_level`, `comp_count`, `geography_used`. **Logic:** comp_based_value = median_ppsf × living_sq_ft; pct_above_comps = (list_price − comp_based_value) / comp_based_value × 100; risk_level: ≤5% low, ≤12% medium, else high.

**Confidence summary:** No separate endpoint; derive from F1 (first row’s comp_count and confidence_band) in the UI.

**Decisions (avoid duplication):**

- **F2 PPSF map** removed: ZIP-level PPSF map is covered by Week 1 `POST /queries/ranked-zips-ppsf` (derive confidence from sale_count in UI) and by `POST /queries/ppsf-map` when analytics exists. See `docs/features/F2_review.md`.
- **F5 Confidence + coverage** removed: Summary is derived from F1 comps in the UI; no separate F5 endpoint.

**Deliverables:**

| Item | Location |
|------|----------|
| Read-only SQL (parameterized + executable) | `sql/readonly/` – f1_comps, f3_offer_range, f4_overpay_risk; see `sql/readonly/README.md` |
| Production views (ZIP-level, no COMMENT) | `sql/production/` – f1_comps, f3_offer_range, f4_overpay_risk |
| Tableau / Web UI plans | `docs/tableau/`, `docs/web_ui/` – F1, F3, F4 (F2/F5 point to ranked-zips or F1) |
| Feature summaries & conventions | `docs/features/` – F1–F4 summaries, F2 review, `CONVENTIONS.md` (no duplicate endpoints) |
| Cursor rule | `.cursor/rules/no-duplicate-features.mdc` – avoid duplicate API/features; derive from existing responses |

### 2.4 Feature feasibility and 7-week schedule

- **Investigate possible vs impossible features** for this project (given current DB, public tables, read-only constraints, and optional external/public data).
- **Schedule feasible features** across the remaining **7 weeks** (Weeks 3–8): each week’s Features (8) in the README reflect this schedule; impossible or Phase-2 items are documented separately (e.g. Phase 2 backlog, data dictionary) rather than blocking the 8-week plan.

### 2.5 Verification

Steps are documented in **`docs/week2-verification.md`**. Run when DB is available.

| Check | Status |
|-------|--------|
| Apply gold: `psql -f sql/gold/parcel_gold.sql`, `transaction_gold.sql` | [ ] |
| Run migrations 001 → 010 → 020 → 030 → 040 → 050 in order | [ ] |
| `python scripts/refresh_mvs.py --concurrently true` completes | [ ] |
| Optional: `--refresh-grid` repopulates `analytics.grid_cells_025` | [ ] |
| `pytest tests/test_row_counts.py` (runs when DB_URL set; skips if not) | [ ] |
| Tableau or API can query `mv_agg_city_year_metrics` and `mv_agg_grid_year_ppsf_025` | [ ] |
| Read-only: `POST /queries/f1/comps`, `f3/offer-range`, `f4/overpay-risk` return expected shapes | [ ] |

---

## 3. Deliverables

1. **Gold:** parcel_gold and transaction_gold views (`sql/gold/parcel_gold.sql`, `transaction_gold.sql`), spec (`notes/parcel_gold_spec.md`), data map (`docs/data-map.md`), tests (`tests/test_row_counts.py`), data-quality memo (`notes/data-quality-memo.md`).
2. **Serving layer:** SQL files `001`–`050`, `041`, `090`; `scripts/refresh_mvs.py`; `docs/serving-layer-README.md`.
3. **Read-only Query Service:** `sql/readonly/` (F1, F3, F4), `sql/production/` views, FastAPI routes, Tableau/web docs, feature conventions (`docs/features/CONVENTIONS.md`), no-duplicate-features rule.
4. **Verification:** `docs/week2-verification.md` (runbook for applying gold and serving layer, running tests).
5. **Feature feasibility and 7-week schedule:** possible vs impossible features investigated; feasible features scheduled across Weeks 3–8 (see README weekly task tables and Features (8) per week).
6. **Week 2 report:** this document (verification checkboxes to be filled when DB is run).

---

## 4. Blockers / Risks

- *Document any schema mismatches (e.g. missing `center_point` or `year_built`), LA boundary vs city-name filter, or refresh timing issues.*
- Read-only features assume public tables (`mls_history`, `property_address`, `street`, `city`) and LA city filter; production views assume analytics schema when available.

---

## 5. Handoff to Week 3

- Gold views and data map feed feasibility and modeling.
- Serving-layer MVs are the source for Tableau dashboards and API aggregates; refresh cadence (e.g. nightly) should be scheduled.
- **Read-only API (F1, F3, F4)** is ready for Tableau and web app when DB has no CREATE rights; use ranked-zips-ppsf or ppsf-map for PPSF map; derive confidence from F1.
- **Conventions:** New features should not duplicate existing responses; see `docs/features/CONVENTIONS.md` and `.cursor/rules/no-duplicate-features.mdc`.
- Week 3 focuses on zoning/feasibility foundations; grid and city×year metrics can be reused for submarket definitions.

**Week 3 plan summary** (full plan: `docs/week3-plan.md`):

- **Objectives:** Understand LA zoning sources (FAR, height, lot coverage, setbacks, parking); translate to constraint-ready fields; implement first `ZoningConstraintBuilder` in `src/feasibility/` (parcel + zoning + geometry → constraints table with e.g. max_gfa_estimate, max_height_ft, min_parking_spaces, max_units); validate geometry coverage (valid center_point/perimeter %, SRID) and document.
- **Deliverables:** Zoning source list and field mapping; feasibility module producing a constraints DataFrame/table; short geometry-coverage note; Week 3 report.
- **Features (8):** Zoning summary, explainable comps, inspection questions by year built, proximity to essentials, setback/height/FAR summary, ADU feasibility check, nearby zoning display, geometry coverage note.
- **Acceptance:** One feasibility script runs for a subset of LA and produces a constraints table; zoning mapping documented.

---

*Update checkboxes and sections as work completes; save as `docs/week2-report.md`.*
