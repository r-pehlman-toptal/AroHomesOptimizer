# Zoning source list and field mapping

**Purpose:** Week 3 deliverable — document LA zoning sources, identify constraint-ready fields (FAR, height, lot coverage, setbacks, parking), and map them to feasibility outputs.

**Last updated:** Week 3.

---

## 1. Current database state

| Table | Key columns | Constraint-related content |
|-------|-------------|----------------------------|
| `property_zoning` | `property_id`, `zone_id` | Parcel–zone association only. |
| `zone` | `id`, `name` | Zone code (e.g. R1, RS, RE, R2, RM). No FAR, height, or setbacks. |

**Gap:** FAR, height, lot coverage, setbacks, and parking are **not** in the current schema. They must come from external sources and be joined by zone code (or a future `staging_zoning` table).

---

## 2. LA zoning sources (possible)

| Source | What it provides | Format / access |
|--------|-------------------|------------------|
| **LAMC (LA Municipal Code)** | Use classifications, density, height, setbacks, parking (narrative) | [LAMC Ch. 1, 12, 13](https://codelibrary.amlegal.com/codes/los_angeles); manual or parsed. |
| **LADBS (Dept of Building & Safety)** | Permit and zoning lookup; sometimes lot-specific | LADBS website / APIs; varies. |
| **LA City Zoning GIS** | Zone boundaries and sometimes attributes | Shapefile / GeoJSON; LA City Planning or LADOT. |
| **ZIMAS (Zoning Info & Map Access System)** | Parcel-level zone, overlays, height district | [zimas.lacity.org](https://zimas.lacity.org) — manual or scrape. |
| **Assessor / parcel data** | Lot dimensions, sometimes zoning code | Already in `property_geometry` (lot_size_sq_ft, vendor dimensions). |

**Impossible or deferred:** Full, authoritative parcel-level FAR/height/setbacks for every LA parcel in one table is not always publicly available; we rely on **zone-code lookup** (typical constraints by zone) until a full import exists.

---

## 3. Field mapping: source → feasibility output

| Constraint field | Source(s) | Notes |
|------------------|-----------|--------|
| **max_gfa_estimate** | FAR × lot_size_sq_ft | FAR from LAMC / zoning table by zone code; lot from `property_geometry.lot_size_sq_ft`. |
| **max_height_ft** | Height district or zone rule | LAMC or zoning layer; often by zone (e.g. R1 30 ft). |
| **min_parking_spaces** | LAMC parking requirements | Per use and zone; e.g. 2 per unit residential. |
| **max_units** | Density / zone | From LAMC or zoning (units per lot or per acre). |
| **front_setback_ft** | LAMC / zoning | Zone- or street-specific. |
| **side_setback_ft** | LAMC / zoning | Typically by zone. |
| **rear_setback_ft** | LAMC / zoning | Typically by zone. |
| **max_lot_coverage_pct** | LAMC / zoning | Some zones set max lot coverage. |

---

## 4. Implementation approach

1. **Short term:** Use a **zone-code lookup table** (e.g. R1, R2, RS, RE, RM → placeholder or typical FAR, height, parking, units). `ZoningConstraintBuilder` joins parcels → `property_zoning` → `zone` to get `zone.name`, then merges the lookup to produce `max_gfa_estimate`, `max_height_ft`, `min_parking_spaces`, `max_units`.
2. **Later:** If `staging_zoning` is populated from LAMC/GIS (parcel_id or zone_code, plus constraint columns), `zoning_gold` and the builder can read from it instead of the lookup.
3. **ADU / overlays:** Document in a separate note; LA ADU rules can drive a stub or rule-based ADU feasibility check once coded.

---

## 5. References

- Data map: `docs/data-map.md` (tables: property_zoning, zone).
- Gold zoning view (when staging exists): `sql/gold/zoning_gold.sql`.
- Feasibility module: `src/feasibility/zoning_constraints.py`.
