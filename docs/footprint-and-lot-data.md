# Footprint and lot data layer

This footprint system measures lot shape (width/depth) and summarizes how lot shapes distribute by ZIP and region so we can connect footprint bands to pricing and liquidity outcomes.

*Focus on home footprint for ideal economics.* We compute (or will compute) median PPSF and DOM by ratio band and by ZIP/submarket to learn which footprints perform best on price and liquidity.

---

## Parcel footprint

**Endpoint:** `POST /queries/parcel-footprint`

For one parcel: returns lot dimensions, **orientation-free aspect_ratio** (max/min, always ≥ 1), **ratio_band** (balanced | moderate | extreme), and **data quality** fields so users can trust or interpret the result.

- **Request body:** `{ "property_id": <int> }`
- **Response:** List of one [ParcelFootprintRow](src/query_service/schemas.py). Always one row; when dimensions are missing or invalid, `is_valid_dimensions` is false and `notes` explains (e.g. "width missing or zero").
- **Width / depth:** Width is frontage (`vendor_lot_width_ft`), depth is lot depth (`vendor_lot_depth_ft`). If inferred columns exist in `property_geometry`, they are used as fallback when vendor is missing.
- **Ratio:** `aspect_ratio = GREATEST(width, depth) / LEAST(width, depth)` (≥ 1). Bands: **balanced** 1.0–1.3, **moderate** 1.3–2.0, **extreme** > 2.0. Legacy `width_to_depth_ratio` (width/depth) is still returned when valid.
- **Data quality:** `width_source`, `depth_source` (`"vendor"` | `"inferred"`), `is_valid_dimensions`, `notes`.
- **Source:** `property_geometry`: `vendor_lot_width_ft`, `vendor_lot_depth_ft`, `lot_size_sq_ft`; optional `inferred_lot_width_ft`, `inferred_lot_depth_ft`.
- **Implementation:** [sql/readonly/parcel_footprint.sql](sql/readonly/parcel_footprint.sql), [src/query_service/queries.py](src/query_service/queries.py) (`parcel_footprint`, `_footprint_ratio_band`).

---

## Lot size buckets

**Endpoint:** `POST /queries/lot-size-buckets`

Lot width/depth bucket counts by ZIP (configurable bucket size in ft). Lets you see the distribution of lot footprints (width × depth) by area.

- **Request body:** Optional `zip_codes` (list), `bucket_size_ft` (default 5). Optional filters: **property_subtype** (e.g. `SINGLE FAMILY RESIDENCE`), **min_lot_size_sq_ft**, **max_lot_size_sq_ft**, **exclude_outliers** (true = exclude width/depth outside 10–250 ft) so distributions are not skewed by condos or non-residential parcels.
- **Response:** List of [LotSizeBucketRow](src/query_service/schemas.py): `zip_code`, `width_bucket`, `depth_bucket`, `lot_count`.
- **Source:** `property_geometry` joined to address for ZIP; filters on non-null, positive width/depth; optional filter by `property_use_standardized` via `mls_history`.
- **Implementation:** [src/query_service/queries.py](src/query_service/queries.py) (`lot_size_buckets`), [src/query_service/schemas.py](src/query_service/schemas.py) (`LotSizeBucketsParams`, `LotSizeBucketRow`).

---

## Analytics lot heatmap

**Endpoint:** `POST /analytics/run/lot-heatmap`

Runs the lot heatmap job with `bucket_mode: "width_depth"` (and optional width/depth bucket size in ft). Persists results to `analytics_lot_heatmap` for dashboards and `GET /analytics/lot-heatmap`.

- **Request body:** Includes **scope** (e.g. `scope: "county_wide"`, **counties**: list), **geo_unit_type** (e.g. `zip`), **market_name** (optional), `bucket_mode`, `width_bucket_ft`, `depth_bucket_ft` (or `lot_size_bucket_sqft` when `bucket_mode` is `lot_size`).
- **Scope:**
  - **Allowed counties:** Typically `LOS ANGELES`, `ORANGE` (and any other counties the job filters on; see [src/analytics/jobs.py](src/analytics/jobs.py) and any allow-list in config or code).
  - **market_name:** Optional label for the run (e.g. `"westside"` for target markets); chosen by the caller. Stored with results for filtering.
  - **ZIP:** The `zip_code` from `property_address` (USPS 5-digit where available). No separate normalized-ZIP table; we use the address table’s `zip_code` as-is.
- **Persistence:** [analytics_lot_heatmap](sql/analytics/analytics_tables.sql): scope, market_name, geo_unit_type, width_bucket_ft, depth_bucket_ft, lot_count, etc.
- **Implementation:** [src/analytics/jobs.py](src/analytics/jobs.py) (`run_lot_heatmap_job`), [src/api/analytics_router.py](src/api/analytics_router.py) (`api_run_lot_heatmap_job`).

---

## Data layer

- **property_geometry** (and [parcel_gold spec](notes/parcel_gold_spec.md)): `vendor_lot_width_ft`, `vendor_lot_depth_ft`, `lot_size_sq_ft` (and optional inferred_* fields).
- **Feasibility** uses `lot_size_sq_ft` for `max_gfa_estimate` (FAR × lot area), so buildable footprint is tied to lot footprint. See [src/feasibility/zoning_constraints.py](src/feasibility/zoning_constraints.py) and [src/query_service/queries.py](src/query_service/queries.py) (`zoning_summary`).

---

## Web UI

- **Property card:** After "Load property", footprint (width×depth, band, aspect) is shown; if invalid, notes/sources are shown.
- **Comps & confidence:** When you "Get comps & confidence", the subject’s lot is shown as *Subject lot: W×D ft (band). Focus on home footprint for ideal economics.* (or notes when invalid).
- **F1 Comps card:** "Lot footprint distribution (this ZIP)" calls lot-size-buckets for the entered ZIP and shows the top 15 width×depth buckets (5 ft increments).
