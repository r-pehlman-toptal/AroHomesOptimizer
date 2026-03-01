# parcel_gold specification

**Purpose:** One row per parcel (property) for LA residential optimization. Feeds feasibility, aggregates (`city_year`), and modeling.

**Canonical key:** `parcel_id` = `property_id` (no separate `property` table; scope from `property_address` and/or `mls_history`).

---

## Column list and source mapping

| Column | Type | Source table.column | Notes |
|--------|------|---------------------|-------|
| `parcel_id` | integer (or PK type) | `property_address.property_id` (driver) | Unique; one row per parcel. |
| `street_id` | integer | `property_address.street_id` | Deterministic: one address per property (e.g. MIN street_id). |
| `zip_code` | varchar | `property_address.zip_code` | From same row as street_id. |
| `city_id` | integer | `street.city_id` | Via street. |
| `city_name` | varchar | `city.name` | Via street → city. |
| `county` | varchar | `city.county` | Via street → city. |
| `center_point_4326` | geometry | `property_geometry.center_point` | One geometry per property (e.g. DISTINCT ON property_id). NULL if no geometry. |
| `lot_size_sq_ft` | numeric | `property_geometry.lot_size_sq_ft` | Optional. |
| `year_built` | integer | `mls_history.year_built` | From latest sale per property (e.g. MAX(sold_date)); NULL if never sold or column missing. |

**Optional columns** (add if present in DB and needed for feasibility/modeling):

| Column | Type | Source table.column | Notes |
|--------|------|---------------------|-------|
| `vendor_lot_width_ft` | numeric | `property_geometry.vendor_lot_width_ft` | |
| `vendor_lot_depth_ft` | numeric | `property_geometry.vendor_lot_depth_ft` | |

---

## Row scope

- **Driver:** Distinct `property_id` from `property_address` (ensures every parcel has an address).  
  Alternative: distinct `property_id` from `mls_history` if only parcels with at least one sale are desired (e.g. for transaction-only analyses).  
  For alignment with `v_fact_sale_clean` and city_year, using **property_address** as driver keeps all addressed parcels; filter by city in view or downstream (e.g. WHERE city_name = 'LOS ANGELES').

- **Deduplication:** One row per `property_id`. Address: pick one per property (e.g. MIN street_id). Geometry: pick one per property (e.g. DISTINCT ON (property_id) ... ORDER BY property_id).

---

## Dependencies

- `property_address`
- `street`
- `city`
- `property_geometry` (LEFT JOIN)
- `mls_history` (LEFT JOIN for year_built; optional subquery for “latest sale per property”)

---

## Implementation file

- **SQL:** `sql/gold/parcel_gold.sql` (CREATE OR REPLACE VIEW or table).  
- **Tests:** Row-count and uniqueness on `parcel_id` in `tests/test_row_counts.py`.
