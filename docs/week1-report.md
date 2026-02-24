# Week 1 Report – LA Residential Design Optimization

**Project:** Aro Homes – LA Market Expansion (Data-Driven Design)  
**Period:** Week 1 of 8  
**Scope:** Project setup, database access, schema discovery, API verification in browser  

---

## 1. Objectives (Week 1)

- Stand up the repository and Python environment.
- Configure and validate connectivity to the `property_data` PostgreSQL database.
- Inventory the database schema (tables, columns, keys) relevant to parcels, MLS, zoning, and geometry.
- Run the API locally and verify at least one Query Service endpoint in the browser (Swagger UI).
- Produce a short data map / memo for handoff to Week 2.

---

## 2. Completed Work

### 2.1 Environment Setup

| Task | Status | Notes |
|------|--------|-------|
| Clone / open repo | Done | Project root: `Aro Homes` |
| Create virtual environment | Done | `python -m venv .venv` |
| Activate venv | Done | `source .venv/bin/activate` (macOS/Linux) |
| Install dependencies | Done | `pip install -r requirements.txt` |

**Key dependencies:** `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `pydantic`, `pandas`, `numpy`, `scikit-learn`, `cvxpy`, others per `requirements.txt`.

### 2.2 Database Configuration

| Task | Status | Notes |
|------|--------|-------|
| Set `DB_URL` | Done | Format: `postgresql+psycopg2://user:password@host/database` |
| Validate connectivity | Done | e.g. `psql "$DB_URL" -c "SELECT 1;"` or API health + one query |
| Identify backbone tables | Done | See Data Map below |

**Connection details (reference only – do not commit secrets):**

- **Host:** `pi-database-prod-rr-1.c2egymwtiilm.us-east-1.rds.amazonaws.com`
- **Database:** `property_data`
- **User:** `postgres`
- **URL:** Set via environment variable `DB_URL`; never store password in code or repo.

### 2.3 Schema Discovery (Data Map)

Relevant tables and columns identified for Query Service and analytics:

| Area | Tables | Key columns / notes |
|------|--------|----------------------|
| **MLS / transactions** | `mls_history` | `property_id`, `sold_price`, `sold_date`, `living_sq_ft`, `bedrooms_total`, `bathrooms_full`, `bathrooms_half`, `property_use_standardized`, `year_built`, `days_on_market` |
| **Address / location** | `property_address` | `property_id`, `street_id`, `zip_code` (1:1 per property via MIN/group in queries) |
| **Street / city** | `street`, `city` | `street.id`, `street.city_id`, `city.id`, `city.name`, `city.county` |
| **Zoning** | `property_zoning`, `zone` | `property_zoning.property_id`, `property_zoning.zone_id`, `zone.id`, `zone.name` (e.g. R1/RS/RE) |
| **Geometry** | `property_geometry` | `property_id`, `vendor_lot_width_ft`, `vendor_lot_depth_ft`, `lot_size_sq_ft` |

**Query Service alignment:** Query A (bed/bath) uses `bedrooms_total`, `bathrooms_full`, `bathrooms_half`; Query D (ranked ZIPs) uses `valid_streets` + county filter; B and C use the tables above.

### 2.4 API Run and Browser Verification

| Task | Status | Notes |
|------|--------|-------|
| Start API | Done | `uvicorn src.api.main:app --reload` |
| Open Swagger UI | Done | `http://127.0.0.1:8000/docs` |
| Call an endpoint from browser | Done | e.g. `POST /queries/bed-bath-distribution` with body `{"city": "LOS ANGELES"}` |
| Confirm JSON response in browser | Done | Response visible in Swagger UI |

**Endpoints verified (at least one):**

- [ ] `GET /health`
- [ ] `POST /queries/bed-bath-distribution`
- [ ] (Optional) `POST /queries/ranked-zips-ppsf`, `POST /queries/lot-size-buckets`, `POST /queries/principal-sfr-zone`

---

## 3. Deliverables

1. **Environment:** Working venv + `requirements.txt` install.
2. **Config:** `DB_URL` documented (in this report or a secure runbook; no secrets in repo).
3. **Data map:** Table/column summary above (or linked doc) for backbone entities.
4. **API verification:** Evidence that the API runs and at least one query returns results in the browser (screenshot or note in report).

---

## 4. Blockers / Risks

- *Document any connection issues, missing tables, or permission problems.*
- *Note if `psql` uses a different user (e.g. OS user) than `DB_URL` – use `DB_URL` for the API.*

---

## 5. Handoff to Week 2

- **Data map** and **backbone tables** feed into design of `parcel_gold` and `transaction_gold` (canonical keys, dedup strategy).
- **API + Swagger** remain the way to run and demo Query Service endpoints; Week 2 adds gold views and tests that may depend on these tables.

---

*Report template can be updated each week; save as `docs/weekN-report.md`.*
