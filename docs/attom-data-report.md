# Attom data report — Aro Homes

**Date:** March 2026  
**Scope:** All Attom API integrations in the Aro Homes application — endpoints used, data fields consumed, features built, data quality observations, and known gaps.

---

## 1. Attom APIs in use

| Endpoint | Method | Used for | Geography |
|----------|--------|----------|-----------|
| `/property/detail` | GET | Single-property lookup by address | Address |
| `/attomavm/detail` (by attomId) | GET | AVM for a specific property | attomId |
| `/attomavm/detail` (by postalCode) | GET | Bulk AVM for all properties in a ZIP | ZIP |
| `/saleshistory/snapshot` | GET | Sale history (price history card) | Address / attomId |
| `/sale/snapshot` | GET | New-build comps (PPSF, DOM); new-build map | ZIP or lat/lon + radius |
| `/property/snapshot` | GET | Target site search; product mix; value accretion | ZIP or lat/lon + radius |

All calls are server-side (API key never exposed to the browser). Pagination is handled transparently via `_attom_get_paged` (up to 500 records total, in 200-record pages).

---

## 2. Features implemented with Attom data

### 2.1 Property details (Attom tab → single property)

Calls `/property/detail` by address. Fields returned and used:

| Category | Fields |
|----------|--------|
| **Identity** | `identifier.obPropId` (Attom ID), `identifier.apn`, `identifier.fips` |
| **Address** | `address.oneLine`, `address.line1/line2`, `address.postal1` (ZIP), `address.locality` (city), `address.countrySubd` (state) |
| **Lot** | `lot.lotsize2` (sq ft), `lot.lotsize1` (acres fallback), `lot.depth`, `lot.frontage` (width) |
| **Building** | `building.size.livingsize` / `universalsize` (living sq ft), `building.rooms.beds/baths`, `building.summary.levels`, `building.construction.condition` |
| **Year built** | `summary.yearbuilt` |
| **Location** | `location.latitude`, `location.longitude` |
| **Valuation** | AVM via `valuation.avm.amount.value`, AVM high/low, `valuation.scr` (confidence), `avm_per_sqft` |
| **Sale** | `sale.amount.saleamt`, `sale.saleTransDate` |
| **Assessment** | `assessment.assessed.assdttlvalue`, `assessment.tax.taxamt/taxyear`, `assessment.market.mktttlvalue` |
| **Property type** | `summary.propsubtype`, `summary.propLandUse` |

**Derived fields** (calculated by our client):
- `suggested_existing_value` — AVM → last sale → sale history (first record), in priority order
- `buildable_width_ft` / `buildable_depth_ft` / `buildable_sq_ft` — lot dimensions minus assumed setbacks (default front 20 ft, rear 20 ft, sides 5 ft each)
- `fits_target_sqft` — true if buildable area ≥ requested target sqft
- `value_per_sqft` — AVM / living sq ft

**Data quality observation:** AVM (`avm_value`) is present for roughly 60–70% of single-property lookups; the rest fall back to last sale amount or sale history. `lot.depth` and `lot.frontage` are returned more often than not for LA properties.

---

### 2.2 Sale history (async card)

Calls `/saleshistory/snapshot` by address. Returns list of sales with:
- `sale_date`, `sale_amount`, `record_date`, `sale_type`
- `price_per_sqft`, `price_per_bed`

Loaded asynchronously after the main property card so the page is fast.

---

### 2.3 Rebuild eval (Attom tab → rebuild evaluation)

Same `/property/detail` call as property details, extended with:
- `gap_to_target_sqft` — how much larger the target is vs. current living sq ft
- Full buildable footprint and `fits_target_sqft` for the requested target size
- Product mix — after eval, client-side product mix table is computed for the specific lot's `buildable_sq_ft`, calling `/new-build-benchmark` for local PPSF

**Existing value fallback chain** (most to least preferred):
1. `suggested_existing_value` from `/rebuild-features` (AVM or last sale)
2. `f.last_sale_amount` or `f.sold_price` from the same response
3. Last-resort: `/sale-history` call for the address → first `sale_amount` (labeled "last sale" in UI)

---

### 2.4 New-build benchmark (Attom)

Calls `/sale/snapshot` with `postalCode` + `minYearBuilt` (default 2020).

Returns for each sale: `living_sq_ft`, `sale_amount`, `days_on_market`, `year_built`.  
Computes: **p25 / median / p75 PPSF** and **p25 / median / p75 DOM**.

`has_new_builds = False` is a negative signal — no new construction in the area since 2020.

**Data quality observation:** Attom frequently returns `days_on_market = 0` or null; DOM percentiles are often unreliable. PPSF data is solid when sale records exist.

---

### 2.5 New-build map

Same `/sale/snapshot` call, but returns per-property records for map rendering:

| Field | Source |
|-------|--------|
| `lat`, `lon` | `location.latitude/longitude` |
| `address` | `address.oneLine` |
| `year_built` | `summary.yearbuilt` |
| `living_sq_ft` | `building.size.livingsize` or `universalsize` |
| `lot_sq_ft` | `lot.lotsize2` |
| `lot_width_ft` | `lot.frontage` |
| `lot_depth_ft` | `lot.depth` |
| `sale_amt` | `saleAmountStnd` or `amount.saleamt` |
| `ppsf` | `sale_amt / living_sq_ft` (filtered: ≥ $100/sqft) |

Map can color by home size, lot size, or PPSF.

---

### 2.6 Target site search

Calls `/property/snapshot` with: `postalCode` (or lat/lon + radius), `maxYearBuilt`, `minUniversalSize`, `maxUniversalSize`.

Per property, extracts:

| Field | Source |
|-------|--------|
| `lat`, `lon` | `location.latitude/longitude` |
| `address` | `address.oneLine` |
| `zip_code` | `address.postal1` |
| `attom_id` | `identifier.obPropId` |
| `year_built` | `summary.yearbuilt` |
| `living_sq_ft` | `building.size.livingsize` / `universalsize` |
| `lot_sq_ft` | `lot.lotsize2` (sq ft) or `lot.lotsize1` × 43,560 (acres→sq ft) |
| `lot_width_ft` | `lot.frontage` |
| `lot_depth_ft` | `lot.depth` |
| `last_sale_amount` | `sale.amount.saleamt` |
| `avm_value` | `avm.amount.value` (rarely populated in snapshot) |

**Buildable footprint estimation:**
- If `lot.frontage` and `lot.depth` are present → exact calculation
- If only `lot_sq_ft` is present → assumes aspect ratio (width ≈ √(lot_sq_ft / 2.2)), then applies setbacks

**Lot depth fallback (recently added):** When `lot.depth` is missing, depth is estimated as `lot_sq_ft / eff_width`. This allows lot-depth percentiles (p25/median/p75) to be populated even when Attom omits the field.

**Data quality observations:**
- `lot.frontage` (width) is present for ~70% of LA snapshot records
- `lot.depth` is present for ~40–50% of records — depth is often estimated
- `lot_sq_ft` (`lotsize2`) is nearly always present
- AVM is rarely populated in `/property/snapshot` — must use bulk `/attomavm/detail` call separately

Aggregate output: total count, buildable count + %, lot-width distribution by bucket (40 ft / 50 ft / 60 ft / 70 ft+ tiers), p25/median/p75 for lot width and depth.

---

### 2.7 Product mix optimizer

Calls:
1. `/property/snapshot` (via `fetch_target_sites_attom`) — same as §2.6
2. `/attomavm/detail?postalCode=…` (via `fetch_bulk_avm_by_zip`) — bulk AVM for the ZIP

**Existing value per property** (priority chain):
1. `snapshot_avm` — from `/property/snapshot` `avm.amount.value` (rarely present)
2. `bulk_avm` — from `/attomavm/detail` postalCode call, joined by `attomId`
3. `last_sale_amount` — from `/property/snapshot` `sale.amount.saleamt`

**New-build PPSF** — from `/sale/snapshot` for the benchmark ZIP.

Sweeps target sizes in-memory (no extra API calls per size). Outputs per size: buildable count, buildable %, new-build value, avg existing value, avg value accretion, total value created.

**Data quality observations:**
- Bulk AVM (`/attomavm/detail`) covers ~85–90% of matched properties in well-covered ZIPs
- Some ZIPs return no AVM — product is shown without existing value in those areas
- Bulk AVM requires a ZIP code; radius-only searches cannot get bulk AVM → "Avg existing value" may be empty

---

### 2.8 Value accretion map

Calls `/property/snapshot` for all target properties, then:
- Collects unique ZIPs from the results
- Parallel-fetches `/sale/snapshot` (new-build PPSF) for each unique ZIP (`ThreadPoolExecutor`)
- Calls `/attomavm/detail` per ZIP for existing values

Per property: `new_build_value = zip_ppsf × target_build_sq_ft`, `value_accretion = new_build_value − existing_value`.

Map is colored by value accretion, new-build value, or local PPSF.

---

## 3. Data availability summary

| Field | API | Availability in LA |
|-------|-----|--------------------|
| Living sq ft | `/property/snapshot`, `/property/detail` | ~95% |
| Lot sq ft | `/property/snapshot`, `/property/detail` | ~90% |
| Lot width (frontage) | `/property/snapshot`, `/property/detail` | ~70% |
| Lot depth | `/property/snapshot`, `/property/detail` | ~40–50% (estimated otherwise) |
| Year built | `/property/snapshot`, `/property/detail` | ~90% |
| Latitude / longitude | All endpoints | ~85% |
| AVM (single property) | `/property/detail` | ~65% |
| AVM (bulk by ZIP) | `/attomavm/detail` | ~85–90% in covered ZIPs |
| Last sale amount | `/property/snapshot` sale block | ~50% |
| New-build PPSF | `/sale/snapshot` year_built ≥ 2020 | Available in most active ZIPs |
| Days on market | `/sale/snapshot` | Present but unreliable (often 0) |
| Zoning / setbacks | — | **Not available** in Attom |

---

## 4. Gaps and limitations

| Gap | Impact | Mitigation |
|-----|--------|------------|
| **No zoning data** | Can't determine true legal setbacks or max GFA | Use configurable assumed setbacks (default 20/20/5 ft); user can override |
| **Lot depth often missing** | Depth percentiles empty; buildable footprint less accurate | Estimate depth = `lot_sq_ft / lot_width` when missing |
| **AVM sparse in `/property/snapshot`** | Product mix existing value column often empty | Use bulk `/attomavm/detail` by ZIP as enrichment layer |
| **Last sale amount** unreliable as existing value proxy | Old sales may not reflect current market | Prioritize AVM; fall back to sale history for single-property eval |
| **DOM data quality** | DOM percentiles unreliable | Display with caveat; filter zero/null values |
| **Radius-only searches lack bulk AVM** | No existing value when no ZIP given | Require ZIP for product mix; show warning |
| **200-record API page limit** | Large areas may be truncated | Paginate transparently up to 500 records; warn user when limit hit |
| **New-build PPSF requires comps** | Thin markets (< 5 new-build sales) give unreliable PPSF | `has_new_builds = False` flag shown in UI; advise caution |

---

## 5. API key and security

- API key stored in `ATTOM_API_KEY` environment variable
- Never sent to or exposed in the browser
- All Attom calls are server-side through FastAPI routes in `src/api/attom_router.py`
- Routes are protected by Cognito auth (`cognito_auth_dependency`)

---

## 6. Code references

| Component | File |
|-----------|------|
| Attom API client (all functions) | `src/attom/client.py` |
| FastAPI endpoints | `src/api/attom_router.py` |
| Buildable footprint estimation | `src/attom/client.py` → `estimate_buildable_footprint()` |
| Pagination helper | `src/attom/client.py` → `_attom_get_paged()` |
| Parallel PPSF fetch | `src/attom/client.py` → `fetch_value_accretion_heatmap_attom()` (ThreadPoolExecutor) |
| Frontend Attom UI | `web/index.html` (Attom tab + Site search panel) |
| API-to-feature mapping | `docs/attom-apis-for-aro-features.md` |
| Property fields reference | `docs/attom-property-details-display.md` |
| Other Attom APIs (bulk, area) | `docs/attom-other-apis.md` |
