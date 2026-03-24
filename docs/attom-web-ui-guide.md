# Attom data — Web UI guide

This guide describes the **Attom** tab in the bundled web app (`web/index.html`), how each screen works, which **API** routes it calls, and how to interpret results. For field-level Attom API mapping, see [attom-property-details-display.md](attom-property-details-display.md).

---

## How to open the UI

1. Run the API locally (from repo root):  
   `uvicorn src.api.main:app --reload`
2. In a browser open: **http://127.0.0.1:8000/app**  
   (Or your deployed host: `https://<host>/app`.)

The UI uses **same-origin** API calls (`API = ''` in `index.html`), so the browser talks to the same host that serves `/app`.

### Attom-only mode (default)

The bundled `web/index.html` is configured for **Attom-only** use:

- `<body class="attom-only-ui">` hides the **city / address / Show region** bar (`#aro-region-bar`).
- There is **no** “Aro homes | Attom” main switcher; **`#sub-nav`** contains only three **Attom** buttons: Property details, Rebuild eval, Site search.
- Aro panels remain in the HTML for possible future use but are not linked from the nav.
- Initial view: **Property details (Attom)**.

To restore the full **Aro + Attom** UI: re-add `<nav id="main-nav">` with both main tabs, re-add the three Aro buttons in `#sub-nav`, unhide `#aro-region-bar` (or remove `attom-only-ui`), set `currentMain` and initial `showSubNavFor` / `showPanelsFor` / `active` panel as needed (see git history).

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **`ATTOM_API_KEY`** | Set in `.env` at repo root (or environment on the server). Without it, Attom endpoints return errors or empty data. |
| **FastAPI routes** | `src/api/main.py` mounts `attom_router` at prefix **`/attom`**. |
| **OpenAPI** | Interactive reference: **http://127.0.0.1:8000/docs** → filter by tag **`attom`**. |

---

## Navigation (Attom-only bundle)

There is a single row of tabs — all **Attom**:

| Tab | Panel id | Focus |
|-----|----------|--------|
| **Property details** | `panel-property-details` | Address lookup, facts, sale history, inline rebuild eval. |
| **Rebuild eval** | `panel-rebuild-eval-attom` | Standalone rebuild eval, new-build benchmark, new-build map. |
| **Site search** | `panel-site-search-attom` | Target sites, product mix, geographic map, exports. |

The internal **Aro (DB)** UI is not shown in this build (no main “Aro | Attom” switcher, no Aro sub-nav buttons).

---

## 1. Property details (Attom)

**Goal:** Look up a single property by **full address** and show normalized Attom fields plus optional sale history and rebuild math.

### Controls

| Control | Element id | Action |
|---------|--------------|--------|
| Address | `attom-address` | Full street address (city, state, ZIP recommended). |
| **Look up** | `btn-attom-lookup` | Loads property details. |

### What loads (UI sections)

1. **Value hero** — Large headline: AVM **or** last sale, labeled “Estimated value” / “Last sale”, or “No value estimate”.
2. **Stats row** — Beds, baths, living sq ft, year built, lot size.
3. **Hero line** — Compact sentence (beds · baths · sqft · lot · year · type).
4. **PPSF / rent** — $/sqft from value÷living area; rough “Est. rent” from a simple rule when data allows.
5. **Home value** — AVM detail (confidence, range, $/sqft) or last sale text.
6. **Facts & features** — Table of address, jurisdiction, rooms, lot dimensions, tax/assessment, coordinates, **Attom ID**.
7. **Price history** — Loaded **asynchronously** after the main response (separate request).
8. **Rebuild eval (Attom)** — Uses the **same** address; set **Target sqft** and click **Run rebuild eval**.

### API calls (from UI)

| User action | Method | Path | Body (JSON) |
|-------------|--------|------|-------------|
| Look up | `POST` | `/attom/property-details` | `{ "address": "<full address>" }` |
| Sale history (auto after lookup) | `POST` | `/attom/sale-history` | `{ "address": "<same address>" }` |
| Rebuild eval (button in panel) | `POST` | `/attom/rebuild-features` | `{ "address": "...", "target_living_sq_ft": <number> }` |

### Tips

- Use a **complete** address string if geocoding is flaky (street, city, state, ZIP).
- If **price history** stays on “Loading…”, check Network tab for `/attom/sale-history` status and response body.

---

## 2. Rebuild eval (Attom) — sub-tab

This sub-tab has **three** cards stacked vertically.

### 2a. Rebuild eval (standalone)

**Goal:** Same rebuild logic as the inline block on Property details, but with its own address field (no need to use Property details first).

| Control | Element id |
|---------|------------|
| Address | `attom-eval-address` |
| Target sqft | `attom-eval-target-sqft` (default 2700) |
| **Run rebuild eval** | `btn-attom-eval-run` |

**API:** `POST /attom/rebuild-features` with `address` and `target_living_sq_ft`.

**Result:** Renders pass/fail for “does target sqft fit buildable footprint?”, buildable width/depth/sqft notes, suggested existing value (AVM vs last sale), and value accretion when benchmark data allows.

---

### 2b. New-build benchmark (Attom)

**Goal:** For one **ZIP**, summarize **new-build** sales (default **year built ≥ 2020**) — PPSF and DOM percentiles from Attom sale snapshot.

| Control | Element id | Typical use |
|---------|------------|-------------|
| ZIP | `nbb-zip` | 5-digit ZIP (required for a focused benchmark). |
| Min year built | `nbb-min-year` | Default 2020 (comps “new build”). |
| Max records | `nbb-page-size` | Caps how many sales are pulled/analyzed (1–200 in UI). |
| **Run benchmark** | `btn-nbb-run` | |

**API:** `POST /attom/new-build-benchmark` — see `/docs` for full schema.

**Interpretation:** UI copy explains that **no new-build sales in the ZIP** is a **negative signal** for new-build pricing in that area.

---

### 2c. New-build map (Attom)

**Goal:** Map **individual new-build sales** as dots; color by size, lot, or PPSF.

| Control | Element id |
|---------|------------|
| ZIP | `nbm-zip` (required) |
| Radius (mi) | Hidden / unused (whole-LA disabled) |
| Min year built | `nbm-min-year` |
| Max records | `nbm-page-size` |
| Color by | `nbm-color-by` — living sqft, lot sqft, or PPSF |
| **Load map** | `btn-nbm-run` |

**API:** `POST /attom/new-build-map`

**Note:** Large `page_size` can still be slow; reduce if needed.

---

## 3. Site search (Attom) — sub-tab

**Goal:** One shared filter set drives **three** parallel analyses:

1. **Target site search (TSS)** — “Teardown” candidate density: older, smaller homes on lots that might fit a **target build sqft** after setbacks.
2. **Product mix (PM)** — Sweep several **target sizes**; rank by total value creation using new-build PPSF and existing values.
3. **Value accretion map (VAM)** — Per-ZIP new-build PPSF baseline and per-parcel **value accretion** on the map when existing value exists.

### Shared filters (top of panel)

| Field | Element id | Meaning |
|-------|------------|---------|
| ZIP | `ss-zip` | **Required** (5-digit or ZIP+4). Whole-LA radius search is disabled in the UI and API to avoid gateway timeouts (504). |
| Radius (mi) | `ss-radius` | Hidden / unused; radius-only search is no longer offered for site search. |
| Max year built | `ss-max-year` | Existing homes **on or before** this year (default 1975 ≈ ~50 yr old). |
| Min / max home sqft | `ss-min-sqft`, `ss-max-sqft` | Filters **current** home living area (default 1100–1700). |
| Target build sqft | `ss-target-sqft` | New home size to test for **fit** on buildable footprint (default 2700). |
| Max records | `ss-page-size` | Page size for Attom snapshot paging (default 200; max 500 per API). |
| Setbacks (ft) | `ss-front-setback`, `ss-rear-setback`, `ss-side-setback` | Used in buildable rectangle math. |

### Product mix–only options

| Field | Element id | Meaning |
|-------|------------|---------|
| Target sizes | `pm-target-sizes` | Comma-separated list (e.g. `2100, 2400, 2700, 3000, 3500`). |
| Benchmark ZIP | `pm-benchmark-zip` | ZIP for **new-build PPSF** benchmark; blank often means “same as filter ZIP” when ZIP is set. |
| Comps since | `pm-comps-year` | Minimum year built for **new-build comps** (default 2020). |
| Min PPSF | `pm-min-ppsf` | Floor on **comp PPSF** for new-build benchmark (default 400); sent as `min_ppsf_comps` to API. |

### Primary action

| Button | Id | Behavior |
|--------|-----|----------|
| **Run all** | `btn-ss-run` | Runs **TSS**, **PM**, and **VAM** in parallel (`Promise.allSettled`). One failure does not always block the others; check each section’s error line. |

### API calls

| Section | `POST` path | Key body fields from UI |
|---------|-------------|---------------------------|
| Target site search | `/attom/target-sites` | **`zip_code` required**; `max_year_built`, `min_living_sq_ft`, `max_living_sq_ft`, `target_build_sq_ft`, setbacks, `page_size` |
| Product mix | `/attom/product-mix` | Same base filters + `target_sizes`, `benchmark_zip_code`, `min_year_built_comps`, `min_ppsf_comps`, `page_size` |
| Value accretion map | `/attom/value-accretion-map` | Same base + `target_build_sq_ft`, `min_year_built_comps`, `min_ppsf_comps`, `page_size` |

Exact JSON shapes match **`AttomTargetSitesRequest`**, **`AttomProductMixRequest`**, **`AttomValueAccretionMapRequest`** in `src/api/attom_router.py`.

### Site search — results UI

**Target site search**

- Summary cards: total matches, buildable count, % buildable, lot width/depth quartiles.
- **Lot-width distribution** chart (Chart.js): buckets; green = fits target, grey = does not.
- **Baseline — new-build PPSF by ZIP** table: filled when VAM returns `zip_benchmarks` (p25/median/p75, sale counts, signals).
- **Geographic map** (Leaflet): dots for properties; **Color by** `tss-color-by`:
  - Buildable sqft, lot size, home size, or **value accretion** (when VAM merged).
- **Buildable only** checkbox filters the map.

**Product mix**

- Benchmark strip + **Product comparison** table.
- **Download product CSV** / **Download properties CSV** — exports for audit (metadata includes `min_ppsf_comps` where applicable).
- **Quantity vs value creation** chart: bars = buildable count, line = avg accretion, ★ = optimal row.

### Why “Min PPSF” appears here but not in raw target-sites

**Target site search** only filters **existing homes** (year, size, geography) and lot/buildable geometry. **Min PPSF** applies to **new-build comp sales** used for benchmarks in **product mix** and **value accretion**, not to the snapshot query for “old small homes.”

---

## Aro tab: Attom enrichment (optional)

On the main **Aro homes** flow, when rebuild eval returns **`attom_improvement_lot`**, the UI can show a small **“Attom: Improvement & lot”** block (`rebuild-eval-attom-wrap`) next to DB-backed sections. That is **not** the Attom tab; it is enrichment when both systems have data.

---

## Troubleshooting

| Symptom | Things to check |
|---------|-------------------|
| Blank errors / “ATTOM_API_KEY not set” | `.env` and server restart; never commit secrets. |
| `401` / `403` on `/attom/*` | Router uses `cognito_auth_dependency` (placeholder in dev). Confirm production auth if enabled. |
| `422` on POST | Missing **`zip_code`** on area endpoints, or other validation (bounds, `page_size` limits). Response `detail` explains. |
| `504` / timeouts | Reduce **`page_size`** or try another ZIP; whole-LA requests are blocked. |
| Site search partial results | **Run all** uses `allSettled` — open browser **Network** and check which of the three calls failed. |
| Map without accretion colors | VAM must succeed and merge into TSS; existing value may be missing for many parcels. |
| New-build map empty | No sales match ZIP/year filters; try another ZIP or adjust **min year built** / **page size**. |

---

## Quick reference — Attom UI → endpoint

| UI area | Endpoint |
|---------|----------|
| Property lookup | `POST /attom/property-details` |
| Sale history | `POST /attom/sale-history` |
| Rebuild features | `POST /attom/rebuild-features` |
| New-build benchmark | `POST /attom/new-build-benchmark` |
| New-build map | `POST /attom/new-build-map` |
| Target sites | `POST /attom/target-sites` |
| Product mix | `POST /attom/product-mix` |
| Value accretion map | `POST /attom/value-accretion-map` |

---

## Related docs

- [attom-property-details-display.md](attom-property-details-display.md) — Field mapping and Attom JSON paths.
- [DEPLOY.md](DEPLOY.md) — Running and deploying the API that serves `/app`.
