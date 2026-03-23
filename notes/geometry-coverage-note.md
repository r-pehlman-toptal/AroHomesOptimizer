# Geometry coverage note

**Purpose:** Week 3 deliverable — document % of parcels with valid center_point and SRID consistency for parcel_gold / property_geometry.

**Last updated:** Week 3.

---

## 1. Scope

- **Parcels:** `parcel_gold` (one row per property_id; driver = property_address).
- **Geometry source:** `property_geometry.center_point` (one per property via geom_one in parcel_gold), exposed as `parcel_gold.center_point_4326`.

---

## 2. Metrics (fill when DB is available)

Run `python scripts/check_geometry_coverage.py` from project root (DB_URL set) to refresh the numbers below.

| Metric | Value | Notes |
|--------|--------|--------|
| Total parcels (parcel_gold) | — | All addressed parcels. |
| Parcels with non-NULL center_point_4326 | — | Has geometry. |
| Parcels with valid (ST_IsValid) center_point | — | Excludes invalid geometries. |
| **Coverage % (valid center_point)** | — | (valid / total) × 100. |
| SRID of center_point (typical) | 4326 | WGS84; grid uses EPSG:3310 (transform in analytics). |

---

## 3. SRID consistency

- **property_geometry.center_point** is expected in WGS84 (SRID 4326). Analytics and grid MVs use `ST_Transform(..., 3310)` for California Albers.
- If any center_point has a different SRID, downstream transforms may be wrong; the check script reports distinct SRIDs seen.

---

## 4. Risks

- Parcels without valid center_point cannot be placed on the 0.25-mile grid or used for distance-based features (e.g. proximity to essentials) until geometry is backfilled or approximated.
- Low coverage in a submarket reduces reliability of grid×year and proximity metrics there.
