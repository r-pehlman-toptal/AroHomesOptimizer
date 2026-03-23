# Data Map – LA Residential Design Optimization

**Purpose:** Canonical reference for backbone tables, primary keys, and join paths. Used by gold views (`parcel_gold`, `transaction_gold`), analytics, and Query Service.

**Last updated:** Week 2 (canonical entities and gold schema).

---

## 1. Backbone and canonical keys

| Concept | Canonical key | Notes |
|--------|----------------|-------|
| **Parcel / property** | `property_id` | One row per parcel. No separate `property` table in current schema; property scope is defined by rows in `property_address` (and/or `mls_history`). |
| **Transaction / sale** | `mls_history.id` | One row per MLS sale; `sale_id` in analytics. |
| **Address** | `property_address.property_id` + `street_id` | One or more addresses per property; use deterministic pick (e.g. MIN street_id) for single-address views. |
| **Street** | `street.id` | `street.city_id` → city. |
| **City** | `city.id` | `city.name`, `city.county`. |
| **Zoning** | `property_zoning.property_id` + `zone_id` | Many-to-many; `zone.name` (e.g. R1, RS, RE). |
| **Geometry** | `property_geometry.property_id` | One geometry per property in practice; use deterministic pick for single-row views. |

---

## 2. Tables and columns (by area)

### 2.1 MLS / transactions

| Table | Primary key | Key columns | Notes |
|-------|-------------|-------------|-------|
| `mls_history` | `id` | `property_id`, `sold_date`, `sold_price`, `living_sq_ft`, `bedrooms_total`, `bathrooms_full`, `bathrooms_half`, `property_use_standardized`, `year_built`, `days_on_market` | One row per sale; join to property via `property_id`. |

### 2.2 Address and location

| Table | Primary key | Key columns | Notes |
|-------|-------------|-------------|-------|
| `property_address` | — | `property_id`, `street_id`, `zip_code` | Use DISTINCT ON (property_id) or MIN(street_id) for one address per property. |
| `street` | `id` | `city_id` | Links address to city. |
| `city` | `id` | `name`, `county` | Filter LA via `UPPER(TRIM(name)) = 'LOS ANGELES'`. |

### 2.3 Zoning

| Table | Primary key | Key columns | Notes |
|-------|-------------|-------------|-------|
| `property_zoning` | — | `property_id`, `zone_id` | Parcel–zone association. |
| `zone` | `id` | `name` | Zone code (e.g. R1, RS, RE). |

### 2.4 Geometry

| Table | Primary key | Key columns | Notes |
|-------|-------------|-------------|-------|
| `property_geometry` | — | `property_id`, `center_point`, `vendor_lot_width_ft`, `vendor_lot_depth_ft`, `lot_size_sq_ft` | Use DISTINCT ON (property_id) for one geometry per property; `center_point` for mapping/grid (transform to EPSG:3310 for grid). |

### 2.5 Property and assessor (tax)

| Table | Primary key | Key columns | Notes |
|-------|-------------|-------------|-------|
| `property` | `id` | `apn`, `tax_id`, `last_update`, `external_update` | One row per parcel. **property.apn has hyphens** (e.g. `2004-013-025`). Use **APN only** to link to assessor data; do not use tax_id for assessor–property linkage. |
| `assessor_parcel` | `id` | `apn`, `roll_year`, `year_built`, `square_footage`, `land_value`, `improvement_value`, `total_value`, `location_latitude`, `location_longitude`, … | LA County Assessor Parcel (tax) data. **Join to property on `property.apn = assessor_parcel.apn`.** Source: Parcel_Data_2021 (etc.); load with `apn` = CSV “Assessor ID” (hyphenated). |

---

## 3. Join paths (gold and analytics)

- **Parcel (one row per property_id):**  
  `property_address` (driver) → `street` → `city`.  
  Optional: `property_geometry` (one row per property_id).  
  Optional: latest or any `mls_history` row per property for `year_built` or similar.

- **Transaction (one row per sale):**  
  `mls_history` → `property_address` (one per property) → `street` → `city`; optional `property_geometry`.

- **Analytics fact (one row per sale, LA only):**  
  `mls_history` JOIN address_one JOIN street_city LEFT JOIN geom_one; filter `city_name = 'LOS ANGELES'`, `sold_price > 0`, `living_sq_ft > 0`.

- **Property ↔ assessor (tax):**  
  `property` JOIN `assessor_parcel` ON `property.apn = assessor_parcel.apn` (apn has hyphens; use Assessor ID from Parcel CSV as apn).

---

## 4. Gold layer alignment

- **parcel_gold:** One row per `property_id`; columns from property_address, street, city, property_geometry; optional valuation/year_built from mls_history or leave null. Key: `parcel_id` = `property_id`.
- **transaction_gold:** One row per `mls_history.id`; columns from mls_history plus derived PPSF; join key to parcel_gold: `parcel_id` = `property_id`. Identifiers: `sale_id` or `transaction_id` = `mls_history.id`.

---

## 5. Query Service alignment

- Bed/bath distribution: `mls_history` (bedrooms_total, bathrooms_full, bathrooms_half) + address + city.
- Ranked ZIPs: `mls_history` + `property_address` + valid_streets (street, city, county).
- Lot-size buckets: `property_geometry` (lot_size_sq_ft or dimensions).
- Principal SFR zone: `property_zoning` + `zone` + address + city.
