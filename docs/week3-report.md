# Week 3 Report – Zoning and feasibility foundations

**Project:** Aro Homes – LA Market Expansion (Data-Driven Design)  
**Period:** Week 3 of 8

---

## Executive summary

Week 3 established zoning and feasibility foundations for the LA market. We documented LA zoning sources and a field mapping from source data to constraint outputs (FAR, height, setbacks, parking). The feasibility module (`ZoningConstraintBuilder`) joins parcel + zoning and produces a constraints table (`max_gfa_estimate`, `max_height_ft`, `min_parking_spaces`, `max_units`) using a zone-code lookup until LAMC/staging data exists. Geometry coverage (valid `center_point`, SRID) is documented and scripted for validation when the DB is available. Eight feature deliverables were implemented or stubbed: zoning summary, explainable comps, inspection questions by year, proximity to essentials, setback/height/FAR summary, ADU feasibility check, nearby zoning, and the geometry-coverage note. Key decisions (one zone per parcel, placeholder lookup, WGS84 center_point) are locked; risks around fan-out, duplicates, sparse comps, and boundary definition are captured with mitigations below.

---

## What I delivered

- **Zoning source list and field mapping** — `docs/zoning-source-and-field-mapping.md`: LA sources (LAMC, ZIMAS, LA City Zoning GIS), current DB state (property_zoning, zone), gap (no constraint columns), and mapping to feasibility outputs.  
  - *Acceptance:* Doc exists; mapping table covers max_gfa_estimate, max_height_ft, min_parking_spaces, max_units, setbacks.

- **Feasibility module (ZoningConstraintBuilder)** — `src/feasibility/zoning_constraints.py`: joins parcel + zoning (one zone per parcel), applies default LA zone lookup, outputs constraints. `scripts/build_constraints.py` loads parcel_gold (LA), property_zoning + zone from DB, runs builder, writes CSV.  
  - *Acceptance:* Builder builds constraints from DataFrames; `python scripts/build_constraints.py --limit 1000` runs and writes CSV when DB available.

- **Geometry coverage note** — `notes/geometry-coverage-note.md` and `scripts/check_geometry_coverage.py`: metrics (total parcels, valid center_point count, coverage %, SRID), risks, and run instructions.  
  - *Acceptance:* Note exists; script runs when DB available and prints summary.

- **Eight Week 3 features** — Each with doc in `docs/features/W3_*.md` and code/SQL as below:

  | # | Feature | Deliverable |
  |---|---------|-------------|
  | 1 | Zoning summary | `sql/readonly/zoning_summary.sql`; `POST /queries/zoning-summary` |
  | 2 | Explainable comps | `src/query_service/explain_comps.py` — `explain_comps_text()` |
  | 3 | Inspection questions by year built | `data/inspection_questions_by_year.yaml`; `src/feasibility/inspection_questions.py` |
  | 4 | Proximity to essentials | `sql/readonly/parcel_center_point.sql`; `POST /queries/parcel-center`; `src/feasibility/proximity.py` |
  | 5 | Setback/height/FAR summary | `src/feasibility/constraint_summary.py` — `format_setback_height_far_summary()` |
  | 6 | ADU feasibility check | `src/feasibility/adu.py` — `check_adu_feasibility()` (stub) |
  | 7 | Nearby zoning display | `sql/readonly/nearby_zoning.sql`; `POST /queries/nearby-zoning` |
  | 8 | Geometry coverage note | See above |

- **Week 3 report** — This document (single merged deliverable).

---

## Key decisions + definitions locked

- **One zone per parcel (for constraints):** Builder uses a single zone per parcel (first from join). Primary-zone or worst-case logic can be added later; for now behavior is defined and consistent.
- **Zone lookup is placeholder:** Default R1/R2/RS/RE/RM values are typical LA placeholders. Replace with LAMC-derived or `staging_zoning` when available; interface (zone code → constraints) stays the same.
- **Constraint fields:** `max_gfa_estimate` (FAR × lot_size_sq_ft), `max_height_ft`, `min_parking_spaces`, `max_units`; setbacks and lot coverage mapped in doc for future use.
- **Center point / SRID:** `property_geometry.center_point` is WGS84 (SRID 4326). Analytics/grid use `ST_Transform(..., 3310)` for California Albers; consistency checked by geometry-coverage script.
- **Parcel driver:** `parcel_gold` driven by property_address; one row per property_id for constraints and coverage stats.

---

## Risks + mitigations

| Risk | Mitigation |
|------|------------|
| **Fan-out** (one parcel → many zones, or many comps) | Constraint builder and zoning summary use one zone per parcel (DISTINCT ON / first). Comps and explainability use existing F1 response; no new fan-out in Week 3. |
| **Duplicates** (same parcel/zone repeated) | Read-only SQL uses `DISTINCT ON (property_id)` for address, geometry, and zoning; APIs return one row per parcel for zoning summary and parcel-center. |
| **Sparse comps** (few or no comps in some areas) | Explainable comps and confidence stay on existing F1 data; UI can derive message from comp_count + confidence_band. No separate sparse-comps endpoint; monitor in Week 4 submarket/archetype work. |
| **Boundary definition** (parcel vs submarket vs grid) | Parcel = property_id (parcel_gold). Submarket and grid boundaries are Week 4 scope; geometry coverage note and center_point validity feed into that. |
| **DB required** | Build and geometry scripts need DB_URL and gold views; they fail cleanly or no-op without DB. Verification checkboxes updated when DB is run. |
| **Low geometry coverage** | Parcels without valid center_point are excluded from grid and distance-based features; coverage % and script documented so backfill or approximation can be prioritized. |

---

## Next week plan + explicit asks

- **Week 4:** Submarket and archetype work; zoning and geometry coverage inform both. Feasibility constraints and ZoningConstraintBuilder feed feature tables for modeling (Week 5).
- **Explicit asks:**  
  - Run `python scripts/build_constraints.py --limit 1000` and `python scripts/check_geometry_coverage.py` when DB is available and tick verification in this report.  
  - Confirm preference on one-zone-per-parcel vs primary/worst-case before expanding zoning data.

---

## Appendix: SQL snippets / implementation details

### Zoning summary (one parcel)

```sql
-- sql/readonly/zoning_summary.sql
-- Parameter: :parcel_id
WITH
addr_one AS (
  SELECT DISTINCT ON (a.property_id) a.property_id, a.street_id
  FROM property_address a ORDER BY a.property_id, a.street_id
),
geom_one AS (
  SELECT DISTINCT ON (pg.property_id) pg.property_id, pg.lot_size_sq_ft
  FROM property_geometry pg ORDER BY pg.property_id
),
zoning_one AS (
  SELECT DISTINCT ON (pz.property_id) pz.property_id, z.name AS zone_code
  FROM property_zoning pz JOIN zone z ON z.id = pz.zone_id ORDER BY pz.property_id
)
SELECT p.property_id AS parcel_id, z.zone_code, g.lot_size_sq_ft
FROM addr_one p
LEFT JOIN zoning_one z ON z.property_id = p.property_id
LEFT JOIN geom_one g ON g.property_id = p.property_id
WHERE p.property_id = :parcel_id;
```

### Nearby zoning (subject + others in same ZIP)

```sql
-- sql/readonly/nearby_zoning.sql
-- Parameters: :parcel_id, :limit
WITH addr_one AS (
  SELECT DISTINCT ON (a.property_id) a.property_id, a.zip_code
  FROM property_address a ORDER BY a.property_id
),
subject_zip AS ( SELECT zip_code FROM addr_one WHERE property_id = :parcel_id LIMIT 1 ),
zoning_one AS (
  SELECT DISTINCT ON (pz.property_id) pz.property_id, z.name AS zone_code
  FROM property_zoning pz JOIN zone z ON z.id = pz.zone_id ORDER BY pz.property_id
),
parcels_in_zip AS (
  SELECT a.property_id AS parcel_id, a.zip_code FROM addr_one a JOIN subject_zip s ON s.zip_code = a.zip_code
),
with_zone AS (
  SELECT p.parcel_id, p.zip_code, z.zone_code FROM parcels_in_zip p LEFT JOIN zoning_one z ON z.property_id = p.parcel_id
)
SELECT parcel_id, zip_code, zone_code, (parcel_id = :parcel_id) AS is_subject
FROM with_zone ORDER BY is_subject DESC, parcel_id LIMIT :limit;
```

### Parcel center point (proximity)

```sql
-- sql/readonly/parcel_center_point.sql
-- Parameter: :parcel_id
SELECT pg.property_id AS parcel_id,
  ST_X(pg.center_point::geometry) AS longitude,
  ST_Y(pg.center_point::geometry) AS latitude
FROM property_geometry pg
WHERE pg.property_id = :parcel_id
  AND pg.center_point IS NOT NULL AND ST_IsValid(pg.center_point::geometry);
```

### Lot heatmap query (analytics)

Core query used in `run_lot_heatmap_job` (`src/analytics/jobs.py`) to bucket parcels by ZIP and lot dimensions/size, then persisted to `analytics_lot_heatmap`:

```sql
WITH address_uniq AS (
    SELECT pa.property_id, MIN(pa.zip_code) AS zip_code
    FROM property_address AS pa
    GROUP BY pa.property_id
),
geom AS (
    SELECT pg.property_id, pg.vendor_lot_width_ft, pg.vendor_lot_depth_ft, pg.lot_size_sq_ft
    FROM property_geometry AS pg
),
joined AS (
    SELECT a.zip_code, g.vendor_lot_width_ft, g.vendor_lot_depth_ft, g.lot_size_sq_ft
    FROM geom AS g
    JOIN address_uniq AS a ON g.property_id = a.property_id
    WHERE a.zip_code IS NOT NULL
)
SELECT
    zip_code,
    CASE WHEN :bucket_mode = 'width_depth' AND vendor_lot_width_ft IS NOT NULL AND vendor_lot_width_ft > 0
         THEN FLOOR(vendor_lot_width_ft / :width_bucket_ft)::int * :width_bucket_ft ELSE NULL END AS width_bucket_ft,
    CASE WHEN :bucket_mode = 'width_depth' AND vendor_lot_depth_ft IS NOT NULL AND vendor_lot_depth_ft > 0
         THEN FLOOR(vendor_lot_depth_ft / :depth_bucket_ft)::int * :depth_bucket_ft ELSE NULL END AS depth_bucket_ft,
    CASE WHEN :bucket_mode = 'lot_size' AND lot_size_sq_ft IS NOT NULL AND lot_size_sq_ft > 0
         THEN FLOOR(lot_size_sq_ft / :lot_size_bucket_sqft)::int * :lot_size_bucket_sqft ELSE NULL END AS lot_size_bucket_sqft,
    COUNT(*) FILTER (WHERE (...)) AS lot_count,
    COUNT(*) FILTER (WHERE ...) AS missing_geom_count
FROM joined
GROUP BY zip_code, width_bucket_ft, depth_bucket_ft, lot_size_bucket_sqft;
```

Full logic and INSERT into `analytics_lot_heatmap` (scope, market_name, geo_unit_type, geo_unit_value, bucket columns, lot_count): `src/analytics/jobs.py` lines 26–130.

---

*Update verification checkboxes when DB is run; save as `docs/week3-report.md`.*
