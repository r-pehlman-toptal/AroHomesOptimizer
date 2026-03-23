## LA Comps & Aggregates – Web UI Tabs

This document explains each major tab and card in `web/index.html`, what the user does there, and which backend APIs are called.

---

## Top controls (always visible)

- **City selector**: `#city-select`
  - Chooses the working city context (e.g. LOS ANGELES, BURBANK).
- **Address or location**: `#address-or-location`
  - Accepts a **Property ID** or **ZIP** (e.g. `12345` or `90012`).
- **Show features in this region**: `#btn-show-region`
  - Resolves the input into a **region** (typically ZIP+city).
  - On success, shows the `By address` / region panel (`#panel-region`) and populates regional features.

---

## Tab: By address (`#panel-region`)

High level: start from a Property ID or ZIP and explore feasibility, comps, where-to-build, and stock (lot/home distributions) for that region.

### Card: Features in this region

- **Purpose**: Intro + summary for the currently selected region.
- **Elements**:
  - `#region-intro-text`: static explanation of how to use the region view.
  - `#region-summary`: short, bold summary once a region is resolved (e.g. which ZIP, how many parcels/comps).
- **Backend**:
  - Driven by the same region-resolution logic as `#btn-show-region` (address/ZIP → region). Uses existing region APIs (no separate endpoint just for the intro card).

### Card: Build size recommendation

- **Purpose**: Recommend **what size home to build** in this region.
- **Elements**:
  - Button `#btn-region-recommend`: triggers a recommendation call.
  - `#region-recommend-result`: main recommendation sentence (e.g. “Target ~2,700 sq ft SFR in 90066.”).
  - `#region-recommend-features`: feature list explaining the recommendation.
- **Backend**:
  - `POST /queries/region-recommend` (pattern): takes region (city + ZIP) and returns recommended target size plus explanatory features.

### Card: Rebuild – Address (feasibility)

- **Purpose**: For a **specific parcel** (Property ID), check if a target size is feasible given zoning and footprint.
- **Elements**:
  - Inputs: `#region-target-sqft`, `#region-product-type` (SFR / Duplex).
  - Button `#btn-region-feasibility`: runs a feasibility check.
  - `#region-feasibility-result`: text result (yes/no + why).
  - `#region-feasibility-error`: error surface (e.g. invalid property ID).
- **Backend**:
  - `POST /queries/feasibility` (pattern): subject property_id + target_sqft + product → feasibility, reasons, and any constraints.

### Card: Comps by ZIP (region)

- **Purpose**: See comps aggregated by ZIP for the selected year within this region.
- **Elements**:
  - Inputs: `#region-comps-year`.
  - Button `#btn-region-comps`.
  - `#region-comps-result`: summary of comps statistics for the region’s ZIP.
  - `#region-comps-error`: error text if call fails.
- **Backend**:
  - `POST /queries/comps-by-zip` (pattern): city + ZIP + year → aggregate comps metrics and short summary.

### Card: Where to build (area ranking)

- **Purpose**: Rank ZIPs or cities by where it is best to build a given product size.
- **Elements**:
  - Inputs: `#region-where-sqft` (target size), `#region-where-geo` (ZIP / City).
  - Button `#btn-region-where`.
  - `#region-where-result`: short text summary of top-ranked areas.
  - `#region-where-table-wrap`: table with rankings and metrics.
- **Backend**:
  - `POST /queries/where-to-build` (pattern): target_sqft + geography → ranking of areas by economics/volume/feasibility.

### Card: New-build benchmark (region)

- **Purpose**: Show recent **new-build PPSF benchmark** for the region.
- **Elements**:
  - Input: `#region-benchmark-year`.
  - Button `#btn-region-benchmark`.
  - `#region-benchmark-result`: summary (new-build PPSF percentiles, count).
- **Backend**:
  - `POST /queries/new-build-benchmark` (pattern): city + ZIP + year → PPSF p25/p50/p75 and sale counts.

### Card: Home size heat map (parcels)

- **Purpose**: Distribution of **home (living) sizes** in the region, filtered by year built.
- **Elements**:
  - Inputs: `#region-homesize-bucket`, `#region-homesize-year-from`, `#region-homesize-year-to`.
  - Button `#btn-region-homesize-heatmap`.
  - `#region-homesize-heatmap-result`: textual summary.
  - `#chart-region-homesize`: Chart.js heat map (or bar-style) visualization.
  - `#region-homesize-heatmap-wrap`: table/grid of bucketed counts.
- **Backend**:
  - `POST /queries/region-home-size-heatmap` (pattern): one row per parcel with living_sq_ft; grouped into buckets by size and year built.

### Card: Lot size heat map (parcels)

- **Purpose**: Distribution of **lot sizes** (sq ft) in the region, filtered by year built.
- **Elements**:
  - Inputs: `#region-lotsize-bucket`, `#region-lotsize-year-from`, `#region-lotsize-year-to`.
  - Button `#btn-region-lotsize-heatmap`.
  - `#region-lotsize-heatmap-result`, `#chart-region-lotsize`, `#region-lotsize-heatmap-wrap` analogous to home-size card.
- **Backend**:
  - `POST /queries/region-lot-size-heatmap` (pattern): parcel-level lot_size_sq_ft buckets.

### Card: Home size × Lot size heat map

- **Purpose**: Joint distribution of **home size vs lot size** (2D matrix of parcel counts).
- **Elements**:
  - Inputs: `#region-homelot-home-bucket`, `#region-homelot-lot-bucket`, `#region-homelot-year-from`, `#region-homelot-year-to`.
  - Button `#btn-region-homelot-heatmap`.
  - `#region-homelot-heatmap-result`, `#region-homelot-heatmap-wrap` show summary and grid.
- **Backend**:
  - `POST /queries/region-home-lot-heatmap` (pattern): parcel-level home+lot, bucketed on both axes.

---

## Tab: Comps & market (`#panel-comps-market`)

High level: property-level comps + confidence, and market-level PPSF/volume views by ZIP and city.

### Card: Property – Comps & confidence

- **Purpose**: Deep dive on one property’s comps and confidence.
- **Elements**:
  - Inputs: `#property-id`, later `#property-sqft`.
  - Button `#btn-load-property`: loads property details.
  - Summaries: `#property-info`, `#property-footprint`, `#property-zoning`, `#property-nearby-zoning`.
  - Confidence panel: `#property-summary`, `#property-confidence`, `#property-confidence-scores`, `#property-confidence-why`, `#property-expected-ppsf`, `#property-speed-to-sell`.
  - Histogram: `#chart-property-ppsf-histogram`.
- **Backend**:
  - `POST /queries/property` (pattern): property_id → MLS + footprint + zoning + nearby zoning.
  - `POST /queries/property-comps` (pattern): property_id + subject_sqft → comps_aggregate + confidence and expected PPSF.

### Card: Comps by ZIP – Table & histogram

- **Purpose**: Show comps table + PPSF histogram for a single ZIP and year.
- **Elements**:
  - Inputs: `#comps-zip`, `#comps-year`, `#comps-limit`.
  - Button `#btn-comps`.
  - Outputs: `#comps-summary`, `#comps-confidence`, `#comps-table-wrap`, `#chart-comps-histogram`.
  - Lot bucket sub-tool: `#lot-bucket-size`, `#btn-lot-buckets`, `#comps-lot-buckets`.
- **Backend**:
  - `POST /queries/comps` (pattern): zip + year → list of comps + aggregate stats + confidence.
  - `POST /queries/lot-footprint-buckets` (pattern): footprint widths/depths by bucket for that ZIP.

### Card: ZIP × Year – Bar (median PPSF by ZIP)

- **Purpose**: Cross-sectional comparison of ZIPs within a year.
- **Elements**:
  - Input: `#zip-year-filter` (year dropdown).
  - Button: `#btn-zip-year`.
  - Chart: `#chart-zip-year-bar`.
- **Backend**:
  - `POST /queries/zip-year-bar` (pattern): returns median PPSF by ZIP for a chosen year.

### Card: Median PPSF by year (one ZIP)

- **Purpose**: Time series of median PPSF for a single ZIP.
- **Elements**:
  - Input: `#zip-trend-zip`.
  - Button: `#btn-zip-trend`.
  - Chart: `#chart-zip-trend`.
- **Backend**:
  - `POST /queries/zip-trend` (pattern): ZIP → yearly median PPSF series.

### Card: City × Year – Median PPSF over time

- **Purpose**: Compare median PPSF trajectories across cities.
- **Elements**:
  - Button: `#btn-city-year`.
  - Chart: `#chart-city-ppsf`.
- **Backend**:
  - `POST /queries/city-year-ppsf` (pattern): city-level median PPSF by year.

### Card: Sales volume over time

- **Purpose**: Sales count trend, typically for the selected city.
- **Elements**:
  - Chart: `#chart-city-volume`.
- **Backend**:
  - `POST /queries/city-volume` (pattern): time-series of sales volume.

### Card: ZIP × Month – Seasonality

- **Purpose**: Seasonality chart (by month) for one ZIP or all ZIPs.
- **Elements**:
  - Input: `#zip-month-zip` (optional).
  - Button: `#btn-zip-month`.
  - Chart: `#chart-zip-month`.
- **Backend**:
  - `POST /queries/zip-month-seasonality` (pattern): median PPSF or volume by month (and optionally ZIP).

### Card: PPSF Map (0.25‑mi grid)

- **Purpose**: Visual PPSF surface over a map, using 0.25‑mile grid cells.
- **Elements**:
  - Leaflet map: `#map`.
  - Year selector and controls live near the card header (see `web/index.html`).
- **Backend**:
  - `POST /queries/ppsf-grid` (pattern): returns grid cells with PPSF metrics; colored blue→green→red by relative PPSF.

---

## Tab: Rebuild (`#panel-rebuild`)

High level: full rebuild evaluation starting from an **address or property ID**, including feasibility, buildable pad, new-build benchmark, and economics.

### Input + run

- **Inputs**:
  - `#rebuild-eval-address`: full address (e.g. `11401 CLOVERST, LOS ANGELES, CA 90046`) or numeric property_id.
  - `#rebuild-eval-zip`: optional ZIP (auto-parsed from the address when present).
  - `#rebuild-eval-target-sqft`: target living_sq_ft for the new build.
- **Button**:
  - `#btn-rebuild-eval`: calls `POST /queries/rebuild-eval`.

### Section: Resolved

- **Elements**:
  - `#rebuild-eval-resolved`: shows property_id, resolved address, and an “OK / invalid” badge plus notes.
- **Backend**:
  - Address resolution: `address_lookup()` (address_text + optional zip/city) → property_id + resolved address.
  - `is_valid` and `notes` indicate missing geometry/zoning or unresolved address.

### Section: Property info (MLS)

- **Elements**:
  - `#rebuild-eval-property-info`: table with latest sale (sold_date, sold_price, PPSF, ZIP, city, year built).
- **Backend**:
  - `property_info()` for the subject property_id.
  - Used for **existing value** in economics.

### Section: Parcel footprint

- **Elements**:
  - `#rebuild-eval-footprint`: lot_size_sq_ft, lot_width_ft, lot_depth_ft, ratio_band, is_valid_dimensions, notes.
- **Backend**:
  - `parcel_footprint()` (read-only SQL): from `property_geometry` and vendor/inferred width/depth.

### Section: Zoning

- **Elements**:
  - `#rebuild-eval-zoning`: zone_code, lot_size_sq_ft (zoning path), max_gfa_estimate, max_height_ft.
- **Backend**:
  - `zoning_summary()`:
    - Uses `_ZONE_LOOKUP` (or inferred FAR from recent sales) to get `max_far` and `max_gfa_estimate`.

### Section: Buildable footprint (lot minus setbacks)

- **Elements**:
  - `#rebuild-eval-buildable`: buildable_width_ft, buildable_depth_ft, buildable_sq_ft, notes.
- **Backend**:
  - `_buildable_footprint_from_zoning()` in `queries.py`:
    - Inputs: `footprint.lot_width_ft`, `footprint.lot_depth_ft`, `zoning.zone_code`.
    - Uses per-zone setbacks from `_ZONE_LOOKUP` (or `_DEFAULT_SETBACKS`) to compute buildable width/depth and area.
  - Surfaced via `RebuildEvalBuildableFootprint` on `RebuildEvalResponse`.

### Section: Feasibility

- **Elements**:
  - `#rebuild-eval-feasibility`: max_gfa_estimate, fits_target_sq_ft, fit_notes.
- **Backend**:
  - `RebuildEvalFeasibilityFit`:
    - `fits_target_sq_ft = (max_gfa_estimate >= target_living_sq_ft)` when max_gfa is present.
    - `fit_notes` explains missing GFA or oversize target vs GFA.

### Section: Comps economics

- **Elements**:
  - `#rebuild-eval-comps`: multi-line summary including:
    - Resale price band (low/base/high) and PPSF (p25/p50/p75).
    - Confidence band/score, comp_count, median distance and recency.
    - New-build price band and PPSF when new-build comps exist.
    - Economics fields (existing_value, value_accretion, build_cost, value_created_vs_build_cost, margin_ratio).
- **Backend**:
  - Resale comps: `comps_aggregate()` for subject parcel and target_sqft.
  - New-build benchmark: `new_build_benchmark()` (zip/city + min_year_built) to derive new-build PPSF and price band.
  - Economics: computed in `rebuild_eval()` using:
    - Existing value from `property_info.sold_price`.
    - Build cost from `build_cost_per_sq_ft × target_living_sq_ft`.
    - New-build value from new-build median PPSF × target_living_sq_ft.

### Section: Neighborhood context (heatmaps)

- **Elements**:
  - Inputs: `#rebuild-eval-year-from`, `#rebuild-eval-year-to`, `#rebuild-eval-lot-bucket`, `#rebuild-eval-home-bucket`.
  - Buttons:
    - `#btn-rebuild-eval-lotsize-heatmap` (lot size).
    - `#btn-rebuild-eval-homesize-heatmap` (home size).
  - Outputs: chart + table for each.
- **Backend**:
  - Reuses the same heatmap endpoints as the region tab, but with **ZIP/city taken from the resolved parcel**:
    - `POST /queries/rebuild-region-lot-size-heatmap`.
    - `POST /queries/rebuild-region-home-size-heatmap`.

---

## Notes for Robert / reviewers

- All UI panels are **read-only** and use **existing read-only SQL + query_service functions**; no new write paths were added.
- The Rebuild tab is the primary surface for:
  - Address resolution → parcel.
  - Zoning and buildable pad.
  - New-build and resale comps benchmarks.
  - Simple economics (value vs build cost).
- Heatmaps and ranking views intentionally reuse aggregations so we **avoid duplicate endpoints**, following the “no duplicate features” rule.

