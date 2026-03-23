# To-do: Extract Attom features for rebuild decisions

**Phase 1: Attom only.** Define and extract rebuild-oriented features from Attom only. No DB/MLS integration yet. Later phases can wire Attom into rebuild_eval or combine with DB.

**Principle: Use APIs at most; when the API doesn’t provide a value, calculate it.** Prefer fields returned by Attom (property/detail, sale-history, etc.). For anything the API doesn’t give (e.g. a single “existing value”, or “gap to target sqft”), derive it from API-sourced fields (e.g. suggested_existing_value = avm → last_sale → first sale; gap_to_target_sqft = target − living_sq_ft; value_per_sqft = avm_value / living_sq_ft).

---

## Phase 1 — Attom only (current scope)

We **only** use Attom. No merge with MLS or DB in this phase.

**Goals:**

1. Define a single **Attom rebuild features** schema (value, improvement, lot, id).
2. Extract those features from the existing Attom normalized property (or from raw property/detail response).
3. Expose via **POST /attom/rebuild-features** (address in → rebuild features out).
4. Optionally show in UI (e.g. Property details tab or a dedicated “Attom rebuild” block).

**Out of scope for Phase 1:**

- Using Attom data inside rebuild_eval (DB-based).
- Fallback rules “MLS vs Attom” or “DB vs Attom”.
- Zoning, comps, or buildable footprint from DB.

---

## Rebuild inputs today (from DB) — for later phases

| Input | Source | Used for |
|-------|--------|----------|
| **existing_value** | `property_info.sold_price` (MLS) | Value accretion, margin vs build cost |
| **property_info** | mls_history: sold_date, sold_price, living_sq_ft, ppsf, zip, city | Subject’s last sale, PPSF |
| **parcel_footprint** | property_geometry: lot_size_sq_ft, lot_width_ft, lot_depth_ft | Buildable pad, feasibility |
| **zoning_summary** | property_zoning + zone: zone_code, max_gfa_estimate | Feasibility, setbacks |
| **comps_economics** | comps_aggregate + new_build_benchmark | PPSF band, new-build value, confidence |

When **MLS has no sale** for the subject, `existing_value` is null and value accretion/margin are missing. When **geometry is missing**, footprint and buildable pad are missing.

---

## Attom features that help rebuild

### 1. Value / economics (existing_value and signals)

| Attom field | Rebuild use |
|-------------|-------------|
| **avm_value** | Use as **existing_value** when `property_info.sold_price` is null (fallback for value accretion, margin). |
| **avm_high**, **avm_low** | Optional range for “value band” and risk messaging. |
| **last_sale_amount**, **last_sale_date** | Alternative last sale when MLS has no row; can drive existing_value. |
| **assessed_value**, **tax_amount**, **tax_year** | Assessor baseline; tax vs value ratio as holding-cost / upside signal. |
| **market_value** (assessor) | Cross-check with AVM when present. |

**Phase 1 to-do (Attom only):**

- [ ] **Define `AttomRebuildFeatures` schema**  
  Value: `avm_value`, `avm_high`, `avm_low`, `avm_confidence`, `last_sale_amount`, `last_sale_date`, `assessed_value`, `tax_amount`, `tax_year`, `market_value`; plus a single **suggested_existing_value** and **suggested_existing_value_source** (e.g. `"avm"` | `"last_sale"` | `"sale_history"`). All from Attom only.

- [ ] **Extract in Attom client**  
  Build rebuild features from normalized property (or raw). Priority for suggested_existing_value: avm_value → last_sale_amount → first sale_history amount. No MLS/DB.

- [ ] *(Later)* Use Attom existing_value in rebuild_eval when MLS missing.

---

### 2. Physical / improvement (subject description)

| Attom field | Rebuild use |
|-------------|-------------|
| **year_built** | Age of improvement; older → stronger rebuild candidate; can filter or weight comps. |
| **living_sq_ft** | Current improvement size; gap vs **target_living_sq_ft** = rebuild scope. |
| **beds**, **baths** | Current configuration vs target product (e.g. 3br vs 4br). |
| **property_type** | SFR vs other; consistency with comps. |

**Phase 1 to-do (Attom only):**

- [ ] **Include in rebuild features**  
  From normalized property: `year_built`, `living_sq_ft` (as current improvement sqft), `beds`, `baths`, `property_type`. No DB.

- [ ] *(Later)* Expose in rebuild_eval or Rebuild tab with “Gap to target”.

---

### 3. Lot / footprint (fallback when DB has no geometry)

| Attom field | Rebuild use |
|-------------|-------------|
| **lot_sq_ft** | Fallback **lot_size_sq_ft** when parcel_footprint is null; approximate max GFA when zoning has FAR (max_gfa ≈ lot_sq_ft × FAR). |

Attom typically does **not** provide lot width/depth; only total lot size. So we cannot derive buildable footprint from Attom alone, but we can improve **feasibility** (max GFA estimate) when we have zoning + Attom lot_sq_ft.

**Phase 1 to-do (Attom only):**

- [ ] **Include `lot_sq_ft` in rebuild features**  
  Already normalized. Add to rebuild export. No zoning/FAR in Phase 1.

- [ ] *(Later)* Use Attom lot_sq_ft + zoning for max_gfa when parcel_footprint missing.

---

### 4. Sale history (context and trend)

| Attom field | Rebuild use |
|-------------|-------------|
| **sale_history** | Multiple sales → price trend, last sale date/amount when MLS missing; price_per_sqft over time. |

**Phase 1 to-do (Attom only):**

- [ ] **Include sale context in rebuild features**  
  e.g. `sale_count`, or `last_sale_date` / `last_sale_amount` / `last_sale_type` (from sale_history or single sale). suggested_existing_value can use first sale when no AVM. Attom only.

- [ ] *(Later)* Fallback order including MLS.

---

### 5. Identification and geocoding

| Attom field | Rebuild use |
|-------------|-------------|
| **latitude**, **longitude** | Geocode when we only have address; needed for comps (subject point) if DB has no property_geometry. |
| **attom_id** | Stable ID for follow-up Attom calls (AVM snapshot, etc.). |

**Phase 1 to-do (Attom only):**

- [ ] **Include `latitude`, `longitude`, `attom_id` in rebuild features**  
  Already in normalized property. Add to rebuild export. No DB geometry in Phase 1.

- [ ] *(Later)* Use Attom lat/lon when property_geometry missing.

---

## Phase 1 implementation order (Attom only)

1. **Define `AttomRebuildFeatures` schema**  
   Value: avm_value, avm_high, avm_low, avm_confidence, last_sale_amount, last_sale_date, assessed_value, tax_amount, tax_year, market_value, **suggested_existing_value**, **suggested_existing_value_source**.  
   Improvement: year_built, living_sq_ft, beds, baths, property_type.  
   Lot: lot_sq_ft.  
   Id: attom_id, latitude, longitude.  
   Sale context: sale_count and/or last_sale_* from sale_history when useful.  
   All fields from Attom only.

2. **Extract in Attom client**  
   Function that takes normalized property (or address → fetch → normalize) and returns `AttomRebuildFeatures`. suggested_existing_value = avm_value else last_sale_amount else first sale_history.sale_amount; source = `"avm"` | `"last_sale"` | `"sale_history"`.

3. **API: POST /attom/rebuild-features**  
   Body: `{ "address": "..." }`. Returns `{ "error" | null, "rebuild_features": AttomRebuildFeatures }`. Attom only.

4. **Optional: UI**  
   Show rebuild features in Property details tab or a small “Rebuild (Attom)” section (value, improvement, lot, suggested_existing_value). No DB/rebuild_eval yet.

5. **Document**  
   List Attom fields in the schema and that Phase 1 is Attom-only.

---

## Phase 1 implemented (Attom-only)

**Principle:** Use APIs at most; when the API doesn't provide a value, calculate it from API-sourced fields.

**API:** `POST /attom/rebuild-features` — Body: `{ "address": "...", "target_living_sq_ft": 2700 }` (target optional). Returns `{ "error" | null, "rebuild_features": AttomRebuildFeatures }`. Data: Attom property/detail only; no DB/MLS.

**Schema:** Value (avm_value, avm_high, avm_low, last_sale_*, assessed_value, tax_*, market_value), **suggested_existing_value** + **suggested_existing_value_source** (calculated), **value_per_sqft** (API or AVM/sqft), **gap_to_target_sqft** (calculated when target given). Improvement (year_built, living_sq_ft, beds, baths, property_type). Lot (lot_sq_ft). Id (attom_id, latitude, longitude). sale_count.

**UI:** Property details tab → "Rebuild (Attom)" → optional target sqft + "Load rebuild features" → table.

---

## Phase 1 checklist (Attom only)

- [x] Define `AttomRebuildFeatures` schema (value, improvement, lot, id, suggested_existing_value + source).
- [x] Extract rebuild features from normalized Attom property in client.
- [x] Add `POST /attom/rebuild-features` (address → rebuild features).
- [x] Optional: show rebuild features in UI.
- [x] Document: Attom-only; no DB/MLS in Phase 1.

---

## Later phases (not in scope for Phase 1)

- [x] **Use Attom existing_value in rebuild_eval when MLS sold_price is null.** Implemented: API layer calls fetch_rebuild_features(resolved_address) when comps_economics.existing_value is null; patches existing_value, existing_value_source="attom", and value_accretion. Schema has existing_value_source ("mls" | "attom"). Rebuild tab shows source next to existing value.
- [x] **Expose Attom improvement + lot in Rebuild tab next to DB data.** Implemented: RebuildEvalResponse.attom_improvement_lot (AttomImprovementLot: living_sq_ft, year_built, beds, baths, lot_sq_ft). API always calls fetch_rebuild_features when resolved_address present; fills attom_improvement_lot when any field present. Rebuild tab shows "Attom: Improvement & lot" section (X sqft · Y beds · Z baths · Built YEAR · Lot W sq ft).
- max_gfa from Attom lot_sq_ft + zoning when parcel_footprint missing.
- Subject lat/lon from Attom when property_geometry missing.
- Document MLS vs Attom fallback order.
