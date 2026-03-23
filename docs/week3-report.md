# Week 3 report – Comps, footprint, zoning and feasibility

**Focus:** Data comps (selection, aggregates, confidence); parcel/lot footprint (orientation-free ratio, data quality, lot-size buckets); zoning and feasibility (constraints, nearby zoning, setback/FAR summary, ADU stub, proximity, inspection questions); geometry coverage.

---

## 1. Comps (comparable sales)

- **F1 Comps** (`POST /queries/f1/comps`): Comparable sales by ZIP and year; each row includes `comp_count` and `confidence_band`. Used for “show me the evidence” and as the basis for confidence summary in the UI.
- **Comps aggregate** (`POST /queries/comps-aggregate`, `POST /queries/comps-aggregate-rows`): Subject-based comps (property ID + living sq ft) with distance and recency; 12‑month window, optional size band (±20%), distance cap (e.g. 2 mi). Returns aggregate metrics (comp_count, median_ppsf, p25/p50/p75, IQR, median_dom) and per-comp rows with `dist_miles`, `months_ago`, weight.
- **Confidence:** Four signals (coverage, proximity, recency, tightness) combined into a 0–1 score and band (High / Medium / Low). Diagnostics (e.g. median months ago, % within 0.25 mi, match rate, IQR, spread ratio) are returned so the UI can explain why confidence is low or high.
- **Explainable comps:** Short text (“same ZIP/cell, same year, similar size; N comps”) generated via `explain_comps_text()` for display in the UI.
- **UI:** Property panel shows comps table, PPSF histogram with p25/p50/p75, confidence band and score, and the “Why” diagnostics; expected PPSF and upside score; speed-to-sell (median DOM). F1 Comps card shows comps by ZIP/year with cohort size and confidence.

**References:** `docs/features/how_much_aggregate.md`, `docs/tableau/visualization_ladder.md`, `docs/features/W3_explainable_comps.md`, `src/query_service/comps_confidence.py`, `sql/readonly/comps_aggregate.sql`, `comps_aggregate_rows.sql`.

---

## 2. Footprint (parcel / lot shape)

- **Parcel footprint** (`POST /queries/parcel-footprint`): For one property, returns lot dimensions, **orientation-free aspect_ratio** (max(width,depth)/min(width,depth), ≥ 1) and **ratio_band**: balanced (1.0–1.3), moderate (1.3–2.0), extreme (>2.0). **Width = frontage** (vendor_lot_width_ft), **depth = lot depth** (vendor_lot_depth_ft). **Data quality:** `width_source`, `depth_source` (vendor | inferred), `is_valid_dimensions`, `notes`. Response is always one row; when dimensions are missing or invalid, `is_valid_dimensions` is false and `notes` explains (e.g. “width missing or zero”).
- **Lot size buckets** (`POST /queries/lot-size-buckets`): Width/depth bucket counts by ZIP (configurable bucket size). Optional filters: **property_subtype** (e.g. SFR), **min_lot_size_sq_ft**, **max_lot_size_sq_ft**, **exclude_outliers** (10–250 ft) so distributions are not skewed by non-residential or odd parcels.
- **Analytics lot heatmap:** `POST /analytics/run/lot-heatmap` with `bucket_mode: "width_depth"`; results stored in `analytics_lot_heatmap` for dashboards.
- **UI:** Property card shows footprint (width×depth, band, aspect) when valid, or notes/sources when invalid. Comps section shows “Subject lot: W×D ft (band). Focus on home footprint for ideal economics.” F1 Comps card has “Lot footprint distribution (this ZIP)” for top width×depth buckets.

**References:** `docs/footprint-and-lot-data.md`, `sql/readonly/parcel_footprint.sql`, `src/query_service/queries.py` (`parcel_footprint`, `lot_size_buckets`), `src/query_service/schemas.py` (`ParcelFootprintRow`, `LotSizeBucketsParams`).

---

## 3. Summary (comps and footprint)

Week 3 delivered: (1) **comps** – subject-based comps, confidence score and diagnostics, explainable comps text, and UI for comps + histogram + confidence; (2) **footprint** – orientation-free aspect_ratio and bands, data quality fields, optional filters on lot-size-buckets, and UI for subject lot and ZIP lot distribution. Documentation is in the referenced docs and in `docs/footprint-and-lot-data.md` (including scope for the heatmap and the “ideal economics” next step).

---

## 4. Zoning and feasibility

- **Zoning summary** (`POST /queries/zoning-summary`): One parcel → zone_code, lot_size_sq_ft, max_gfa_estimate, max_height_ft, min_parking_spaces, max_units. Uses property_zoning + zone and applies LA zone-code lookup (R1, R2, RS, RE, RM) in `src/feasibility/zoning_constraints.py` and `queries.py`.
- **Nearby zoning** (`POST /queries/nearby-zoning`): Subject parcel + other parcels in same ZIP with zone_code and is_subject; supports “Subject: R1” and “Nearby: R1, R2, …” in UI.
- **Setback/height/FAR summary:** `format_setback_height_far_summary()` in `src/feasibility/constraint_summary.py` formats zoning-summary (and optional setbacks) as one-line text for display.
- **ADU feasibility:** Stub in `src/feasibility/adu.py` (`check_adu_feasibility()`); returns status="stub" until LA ADU rules are in DB/code.
- **Proximity to essentials:** `POST /queries/parcel-center` returns parcel lon/lat; `src/feasibility/proximity.py` provides `distances_to_pois()` and `nearest_poi_stub()`; external POI (groceries, hospitals, parks) required for live distances.
- **Inspection questions by year built:** `src/feasibility/inspection_questions.py` with `data/inspection_questions_by_year.yaml`; `get_inspection_questions(year_built)` and `get_inspection_band_label(year_built)` for UI.

**References:** `docs/features/W3_zoning_summary.md`, `docs/features/W3_nearby_zoning.md`, `docs/features/W3_setback_height_far_summary.md`, `docs/features/W3_adu_feasibility.md`, `docs/features/W3_proximity_to_essentials.md`, `docs/features/W3_inspection_questions.md`, `docs/zoning-source-and-field-mapping.md`, `src/feasibility/zoning_constraints.py`, `sql/readonly/zoning_summary.sql`, `sql/readonly/nearby_zoning.sql`.

---

## 5. Geometry coverage

- **Note:** `notes/geometry-coverage-note.md` documents % parcels with valid center_point and SRID consistency for parcel_gold / property_geometry.
- **Script:** `scripts/check_geometry_coverage.py` prints coverage and SRIDs when run against the DB.

**References:** `docs/features/W3_geometry_coverage_note.md`, `notes/geometry-coverage-note.md`, `scripts/check_geometry_coverage.py`.

---

## 6. Week 3 completion summary

Week 3 is complete. Delivered: **(1) comps** – subject-based comps, confidence and explainable text, UI; **(2) footprint** – aspect_ratio and bands, data quality, lot-size-buckets and UI; **(3) zoning and feasibility** – zoning summary and nearby zoning APIs, constraint formatter, ADU stub, proximity helpers, inspection questions by year built; **(4) geometry coverage** – note and check script. All eight Week 3 features are implemented (as stubs where noted). Zoning mapping is in `docs/zoning-source-and-field-mapping.md`; feasibility module in `src/feasibility/`; Week 3 report is this document.
