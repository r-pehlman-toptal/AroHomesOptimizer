LA Residential Design Optimization – Analytics Skeleton
======================================================

This repository is a working skeleton for a **Principal Data Scientist / Applied Optimization Consultant** focused on defining optimal residential designs for the **Los Angeles** market. It is designed to move from intuition‑driven to **data‑driven, constraint‑aware** design decisions.

The structure and conventions below are tuned for:

- **Integrating messy urban data** (tax assessor, MLS, zoning/planning, parcel geometry).
- **Translating zoning and physical constraints into optimization models**.
- **Quantifying market fit** (price per square foot, days on market, absorption).
- **Communicating trade‑offs** to non‑technical stakeholders through decision‑oriented outputs.


Project Layout
--------------

```text
src/
  db/              # DB connections, query runner, typed access helpers
  etl/             # Gold tables + aggregates materialization
  feasibility/     # Zoning/physical constraints → model‑ready features
  models/          # Pricing/DOM models, optimization workflows

sql/
  gold/            # Canonical joins across core LA datasets
  agg/             # Aggregations (city_year, submarket_year, grid_year, etc.)

tests/             # Row‑count + duplication checks, basic data quality
requirements.txt   # Core Python dependencies
```


Conceptual Data Flow
--------------------

1. **Raw data ingestion (outside this repo or upstream)**  
   - Tax assessor records (APNs, square footage, year built, use codes, etc.).  
   - MLS transactions and current listings.  
   - Zoning and planning datasets (use, height, FAR, set‑backs, overlays).  
   - Parcel geometries (polygons, centroids, lot metrics).

2. **Gold tables (`sql/gold`, `src/etl`)**  
   - Canonical, de‑duplicated, and consistently keyed tables for:
     - `parcel_gold`: one record per parcel, linked to assessor + geometry.
     - `transaction_gold`: normalized MLS/transaction data with prices, DOM.
     - `zoning_gold`: parcel‑level zoning attributes and constraints.
   - Implemented as SQL views or materialized tables, orchestrated via Python ETL runners.

3. **Aggregates (`sql/agg`, `src/etl`)**  
   - Submarket‑level summaries by **city/region**, **neighborhood**, or **custom grid cells**:
     - `city_year`, `submarket_year`, `grid_year`, etc.
     - Metrics such as median price per square foot, days on market, inventory, and absorption.

4. **Feasibility / constraints layer (`src/feasibility`)**  
   - Translates zoning and physical rules into **feasible building envelopes**:
     - Lot coverage, FAR, height limits, setbacks, parking minimums, unit count caps, etc.
   - Outputs **scenario‑ready envelopes** that can be fed into optimization:
     - Max GFA, typical buildable area after constraints, feasible unit mixes, parking layouts.

5. **Models & optimization (`src/models`)**  
   - **Baseline predictive models** (e.g., price per square foot, DOM):
     - Feature‑engineered from gold + aggregates + feasibility outputs.
   - **Constraint‑based optimization**:
     - Objective functions such as NPV, IRR, or expected profit.
     - Decision variables such as unit mix, square footage allocations, parking count.
     - Zoning/physical rules imported from the feasibility layer as constraints.

6. **Decision‑oriented outputs**  
   - Recommended ranges and ratios (e.g., unit mix ratios, target size bands, parking/unit).  
   - Submarket‑specific design templates and “guardrails”.  
   - Scenario and sensitivity charts that expose trade‑offs to non‑technical stakeholders.


How This Maps to the Principal DS / Optimization Role
-----------------------------------------------------

- **Integrate diverse datasets**  
  - Implemented via `src/db` (connections, query runner) and `sql/gold` canonical joins.  
  - The consultant is expected to:
    - Source and normalize LA‑specific tax assessor, MLS, zoning, and geometry data.
    - Define primary keys and deduplication logic (e.g., parcel/APN, listing IDs).

- **Develop constraint‑based optimization models**  
  - Centered in `src/feasibility` (zoning → constraints) and `src/models` (optimizers).  
  - Use Python optimization libraries (e.g., `cvxpy`, `pyomo`, or similar) to:
    - Encode lot‑level constraints.
    - Solve for designs that maximize a chosen objective (e.g., profit, NPV, yield on cost).

- **Conduct scenario & sensitivity analyses across LA submarkets**  
  - Leveraging `sql/agg` and `src/models`:
    - Run what‑if scenarios by submarket, zoning class, and typology.
    - Stress‑test assumptions (rents, costs, absorption) and produce sensitivity plots.

- **Translate results into clear, defensible design recommendations**  
  - Emphasis on **decision‑oriented ranges** rather than black‑box scores:
    - Target unit count ranges.
    - Recommended unit size distributions.
    - Suggested parking ratios by submarket and typology.

- **Solve unique commercial data problems**  
  - Patterns in messy LA data (e.g., non‑standard zoning overlays, partial parcels, atypical MLS listings) are handled in:
    - `src/etl` (data cleaning, imputation, validation).
    - `tests/` (row‑count and duplication checks).


8-Week Plan (Detailed)
----------------------

Assumes ~20 hrs/week; adjust scope if capacity differs.

---

### Week 1 – Setup, access, and first run

**Objectives:** Repo usable, DB reachable, schema understood, API runnable and verifiable in the browser.

| Task | Deliverable |
|------|-------------|
| Create venv, install `requirements.txt` | Working Python environment |
| Set `DB_URL` (env or .env); validate connection | DB connectivity confirmed (e.g. `psql` or API health) |
| Run `information_schema` or client tool to list tables/columns for property, MLS, address, street, city, zoning, geometry | **Data map**: list of backbone tables, primary keys, and how they join |
| Start API: `uvicorn src.api.main:app --reload` | API runs without import/connection errors |
| Open `http://127.0.0.1:8000/docs`, call e.g. `POST /queries/bed-bath-distribution` with `{"city": "LOS ANGELES"}` | JSON response visible in Swagger UI (browser verification) |
| Write short Week 1 report (data map, what was verified, any blockers) | **Week 1 report** (e.g. `docs/week1-report.md`) |

**Acceptance:** You can open the docs UI, execute one query endpoint, and see results in the browser; data map exists for handoff to Week 2.

---

### Week 2 – Canonical entities, gold schema, and serving layer

**Objectives:** Define and implement first gold views; lock in backbone tables and keys; add basic tests; **and** deliver the production-ready Postgres/PostGIS serving layer (one-row-per-sale fact, filtered LA MV, city×year and grid×year aggregates, refresh script) for Tableau and API.

| Task | Deliverable |
|------|-------------|
| Choose “property backbone” table and key (e.g. `property_id`); document in data map | Updated data map with chosen tables/keys |
| Design `parcel_gold` columns (IDs, location, land/physical, geometry, valuation); document source table.column per column | **parcel_gold spec** (e.g. `notes/parcel_gold_spec.md`) |
| Implement `sql/gold/parcel_gold.sql` (view or table) joining property + address + geometry + valuation as needed | Working `parcel_gold` view/table |
| Design `transaction_gold` (one row per transaction; price, DOM, PPSF, beds/baths, living_sq_ft); implement `sql/gold/transaction_gold.sql` | Working `transaction_gold` view/table |
| Add row-count and uniqueness tests (e.g. `tests/test_row_counts.py`) for parcel and transaction gold | Tests run (can be skipped if DB not in CI) |
| Profile key columns (nulls, distributions); note 2–3 data quality risks | Short data-quality memo in report or notes |
| **Serving layer:** Create `analytics` schema; `v_fact_sale_clean` (one row per sale, no fan-out, LA); `mv_sale_la_since2020_ppsf400` (filters: sold_date ≥ 2020-01-01, ppsf ≥ 400) with unique + B-tree + GiST indexes | `sql/001_create_schema.sql`, `010_v_fact_sale_clean.sql`, `020_mv_sale_la_since2020_ppsf400.sql` |
| **Serving layer:** City×year MV (`mv_agg_city_year_metrics`) and 0.25-mile grid table + grid×year MV (`grid_cells_025`, `mv_agg_grid_year_ppsf_025`) in EPSG:3310, with indexes for concurrent refresh | `sql/030`, `040`, `041`, `050` |
| **Serving layer:** Python script to refresh MVs in dependency order (`--concurrently`, `--refresh-grid`), plus README (assumptions, indexes, cadence, Tableau usage) | `scripts/refresh_mvs.py`, `docs/serving-layer-README.md` |
| Write Week 2 report | **Week 2 report** (e.g. `docs/week2-report.md`) |

**Acceptance:** Gold views exist and return data; tests exist; spec and data-quality notes are written; **and** serving-layer SQL + script + README are in place, MVs refresh successfully, and Tableau/API can query city×year and grid×year aggregates.

---

### Week 3 – Zoning and feasibility foundations

**Objectives:** Understand LA zoning sources; translate zoning into constraint-ready fields; validate geometry coverage.

| Task | Deliverable |
|------|-------------|
| Gather LA zoning/planning docs or existing zoning layers; identify FAR, height, lot coverage, setbacks, parking | Zoning source list and field mapping |
| Implement first version of `ZoningConstraintBuilder` in `src/feasibility/`: join parcel + zoning + geometry; output placeholder or real `max_gfa_estimate`, `max_height_ft`, `min_parking_spaces`, `max_units` | Feasibility module that produces a constraints DataFrame/table |
| Check geometry: % parcels with valid `center_point` or `perimeter`; SRID consistency | Short geometry-coverage note |
| Write Week 3 report | **Week 3 report** |

**Acceptance:** One feasibility script runs for a subset of LA and produces a constraints table; zoning mapping is documented.

---

### Week 4 – Aggregations and submarket lens

**Objectives:** Define LA submarkets; build aggregate views; exploratory analysis by submarket/typology.

| Task | Deliverable |
|------|-------------|
| Define submarkets (city, neighborhood, macro/micro, or grid); choose canonical geography for analysis | Submarket definition (list or config) |
| Implement `sql/agg/city_year`, `submarket_year` (or `grid_year`) with metrics: median/mean PPSF, DOM, volume | Working agg views |
| Use SQL + Python to compare distributions across submarkets and typologies (SFR vs small multifamily) | Exploratory notebook or script with 2–3 charts/tables |
| Propose 3–4 “LA product archetypes” (unit mixes/size bands) to focus optimization on | Short archetype list in report or notes |
| Write Week 4 report | **Week 4 report** |

**Acceptance:** Agg views exist and are queryable; one exploratory artifact and archetype list exist.

---

### Week 5 – Baseline price and DOM models

**Objectives:** Feature tables from gold + aggregates + feasibility; train baseline PPSF and DOM models; document performance and caveats.

| Task | Deliverable |
|------|-------------|
| Build feature table (location, physical, zoning/feasibility) for modeling | Feature pipeline or notebook |
| Implement or extend `BaselineMarketModels` in `src/models/`: regressions for `price_per_sqft` and `days_on_market`; K-fold CV | Trained baseline models (script or notebook) |
| Feature importance or coefficients; residual checks by submarket/typology | Model card: performance, safe-use ranges, caveats |
| Write Week 5 report | **Week 5 report** |

**Acceptance:** Baseline models train and predict; model card exists.

---

### Week 6 – Site-level design optimization prototype

**Objectives:** Formalize single-site optimization; implement optimizer using feasibility constraints and baseline revenue expectations; run on example sites.

| Task | Deliverable |
|------|-------------|
| Write optimization formulation: decision variables (unit counts, GFA, parking), objective (e.g. revenue or margin proxy), constraints from feasibility | One-page formulation or doc |
| Implement or extend `SimpleEnvelopeOptimizer` in `src/models/design_optimization.py`: bind feasibility constraints per parcel; plug in PPSF/revenue from baseline | Working optimizer for one site |
| Add scenario hooks: vary price ±X%, cost or parking; output scenario table per parcel | Scenario script or notebook |
| Run optimizer on 2–3 representative LA sites; document recommended unit mix and objective | Example outputs in report or notebook |
| Write Week 6 report | **Week 6 report** |

**Acceptance:** Optimizer runs on example sites and returns unit mix + objective; at least one scenario variant is run.

---

### Week 7 – Scenario analysis and stakeholder-ready outputs

**Objectives:** Run optimization across a curated set of parcels; produce decision-oriented views and simple visualizations; draft design playbook.

| Task | Deliverable |
|------|-------------|
| Run optimizer (or batch) on a sample of parcels across multiple LA submarkets | Scenario table: parcel/submarket, optimal mix, objective |
| Build scenario grids (e.g. price ±10–20%, cost ±10–20%); sensitivity curves for key sites | Sensitivity tables or charts |
| Create SQL views or notebooks for: recommended unit count ranges, size bands, parking ratios by submarket | Decision-oriented outputs (tables/charts) |
| Draft “LA Design Playbook v0”: 3–5 headline recommendations, supported by outputs | **Playbook v0** (slides or memo) |
| Write Week 7 report | **Week 7 report** |

**Acceptance:** Scenario and sensitivity outputs exist; Playbook v0 is presentable.

---

### Week 8 – Hardening, documentation, and handoff

**Objectives:** Repo ready for handoff; pipelines and assumptions documented; stakeholder walkthrough and Phase 2 backlog.

| Task | Deliverable |
|------|-------------|
| Solidify entry points: CLI or notebook to rebuild gold/agg, run feasibility, run optimization on a set of parcels | Runbook or README section: how to run E2E |
| Add or extend tests: row-count/duplication for gold/agg; guardrails on model inputs | Test suite documented and runnable |
| Expand README: data dictionary for gold/agg/constraints, assumptions, known limitations | Updated README and optional data dictionary |
| Stakeholder walkthrough: present insights, playbook, live demo of scenario/optimization | Walkthrough completed; feedback captured |
| Capture Phase 2 backlog (e.g. cost model, more zoning, dashboard) | **Phase 2 backlog** (list or doc) |
| Write Week 8 report | **Week 8 report** |

**Acceptance:** Repo is documented and runnable; Playbook and Phase 2 backlog are agreed with stakeholders.


Getting Started
---------------

### 1. Environment setup

Create a virtual environment and install dependencies:

```bash
cd "Aro Homes"
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

You can adjust or pin versions in `requirements.txt` as needed.


### 2. Database & connections

- Configure your database connection settings via environment variables (e.g., `DB_URL`) or a small config file used by `src/db/connection.py`.  
- The query runner will be responsible for:
  - Executing the SQL in `sql/gold` and `sql/agg`.
  - Materializing views/tables to be consumed by ETL and modeling code.


### 3. Running ETL to build gold tables

Typical workflow (to be implemented in `src/etl`):

1. Pull raw data into staging tables or files (e.g., S3, CSVs, or raw schemas).  
2. Run `sql/gold/*.sql` to create standardized, de‑duplicated gold views/tables.  
3. Run `sql/agg/*.sql` to compute aggregates at city, submarket, or grid levels.  
4. Use Python scripts in `src/etl` to:
   - Validate row counts and uniqueness (with tests in `tests/`).  
   - Export feature tables for modeling and optimization.


### 4. Feasibility & zoning constraints

- Implement a core class (e.g., `ZoningConstraintBuilder`) under `src/feasibility/` that:
  - Reads parcel + zoning records from the gold tables.
  - Computes feasible envelopes (e.g., max buildable area, envelope geometry summaries).
  - Encodes constraints in a form suitable for optimization libraries.


### 5. Modeling & optimization

- In `src/models/`:
  - Start with regression models correlating **market features** to:
    - Price per square foot.
    - Days on market.
  - Layer on optimization routines that:
    - Take feasible envelopes and cost assumptions.
    - Choose unit mixes and sizes subject to constraints.
    - Output design recommendations and sensitivity analyses.


### 6. API & Query Service

The project exposes a FastAPI application that provides:

- `GET /health` – simple liveness check.  
- Query Service endpoints under `/queries/*` for productionized SQL, e.g.:
  - `POST /queries/bed-bath-distribution`
  - `POST /queries/principal-sfr-zone`
  - `POST /queries/lot-size-buckets`
  - `POST /queries/ranked-zips-ppsf`
- Analytics endpoints under `/analytics/*` for precomputed market-expansion outputs, e.g.:
  - `POST /analytics/run/regression` – run a regression job and store coefficients.  
  - `POST /analytics/run/home-size-scenarios` – compute home-size scenarios from a regression run.  
  - `POST /analytics/run/lot-heatmap` – persist lot-size heatmap buckets.  
  - `POST /analytics/run/value-map` – persist value maps by ZIP/city.  
  - `GET /analytics/*` – fetch stored analytics for dashboards.

To run the API locally (after setting `DB_URL`):

```bash
uvicorn src.api.main:app --reload
```

You can then hit endpoints with any HTTP client. For example:

```bash
curl -X POST http://localhost:8000/queries/bed-bath-distribution \
  -H "Content-Type: application/json" \
  -d '{"city": "LOS ANGELES"}'
```


### 7. Analytics jobs (Market Expansion)

The analytics job layer in `src/analytics/` computes and persists:

- **Regression runs** (`analytics_regression_runs`) with coefficients and sample metadata.  
- **Home-size scenarios** (`analytics_home_size_scenarios`) for size ranges (e.g. 2000–3000 sqft).  
- **Lot heatmaps** (`analytics_lot_heatmap`) for lot width/depth or lot-size buckets.  
- **Value maps** (`analytics_value_maps`) for estimated value and value per sqft by geo unit.

Typical workflow:

1. Run the analytics DDL once to create tables:

   ```bash
   psql "$DB_URL" -f sql/analytics/analytics_tables.sql
   ```

2. Trigger jobs via the API:

   - Run a regression and get its ID:

     ```bash
     curl -X POST http://localhost:8000/analytics/run/regression \
       -H "Content-Type: application/json" \
       -d '{
         "scope": { "scope": "county_wide", "counties": ["LOS ANGELES", "ORANGE"] },
         "date_range_start": "2015-01-01",
         "property_use": "SINGLE FAMILY RESIDENCE"
       }'
     ```

   - Use the returned `id` to compute home-size scenarios:

     ```bash
     curl -X POST http://localhost:8000/analytics/run/home-size-scenarios \
       -H "Content-Type: application/json" \
       -d '{ "regression_run_id": 1, "size_min": 2000, "size_max": 3000, "size_step": 100 }'
     ```

   - Generate lot heatmaps and value maps:

     ```bash
     curl -X POST http://localhost:8000/analytics/run/lot-heatmap \
       -H "Content-Type: application/json" \
       -d '{
         "scope": { "scope": "county_wide", "counties": ["LOS ANGELES", "ORANGE"] },
         "geo_unit_type": "zip",
         "bucket_mode": "width_depth",
         "width_bucket_ft": 5,
         "depth_bucket_ft": 5
       }'

     curl -X POST http://localhost:8000/analytics/run/value-map \
       -H "Content-Type: application/json" \
       -d '{
         "scope": { "scope": "county_wide", "counties": ["LOS ANGELES", "ORANGE"] },
         "geo_unit_type": "zip",
         "date_range_start": "2015-01-01",
         "property_use": "SINGLE FAMILY RESIDENCE"
       }'
     ```

3. The frontend can then consume the stored analytics via:

   - `GET /analytics/regression-runs/{id}`  
   - `GET /analytics/home-size-scenarios?regression_run_id={id}`  
   - `GET /analytics/lot-heatmap?...`  
   - `GET /analytics/value-maps?...`


### 8. Visualization & stakeholder communication

- Use SQL (with clear, parameterized queries) plus Python notebooks or scripts to:
  - Visualize submarket‑level performance and design trade‑offs.
  - Show how zoning and design choices impact price and DOM.
- Focus outputs around **defensible, explainable ranges** and **clear trade‑off charts**.


Testing & Data Quality
----------------------

- `tests/` is reserved for:
  - Row‑count checks between staging and gold tables.
  - Duplication and key‑integrity checks (e.g., unique parcel IDs).  
  - Simple sanity checks on distributions (e.g., no negative square footage, valid price ranges).

The initial repository is intentionally lightweight; the Principal Data Scientist / Applied Optimization Consultant will:

- Own the details of feature engineering, model selection, and optimization formulation.  
- Evolve the SQL and Python modules to reflect LA‑specific reality and business needs.  
- Maintain a clear audit trail of assumptions and decisions in both code and documentation.

