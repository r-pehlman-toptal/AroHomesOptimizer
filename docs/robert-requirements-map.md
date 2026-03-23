# Robert's requirements – map to codebase and UI

This doc maps Robert's product/strategy asks to existing capabilities, where to find them in the UI, and what’s missing.

---

## 1. Density of target pockets (50 years old, ~1,400 sq ft, buildable lots)

**Ask:** Find density/incidence of homes that are **50 years old** and **~1,400 sq ft** on lots we know we can build on → “pockets of attractive target areas.”

**In codebase:**
- **`site_search()`** + **`SiteSearchParams`** already support:
  - **`max_year_built`** (e.g. 1975 for 50+ years old)
  - **`min_living_sq_ft`** / **`max_living_sq_ft`** (e.g. 1200–1600 for ~1,400)
  - **`target_sqft`** (e.g. 2700) so only parcels that **can fit** that product are returned (zoning + lot dimensions + buildable footprint).
- **API:** `POST /decisions/site-search` (in `decisions_router.py`).

**In UI:** There is **no dedicated “Site search” or “Target pipeline” tab/card** in the nav. So you **can’t find** this in the UI today; it’s only callable via API (e.g. Swagger at `/docs` → `POST /decisions/site-search`).

**Suggested next step:** Add a card (e.g. on **Rebuild** or **By address**) to run site search with:
- Target sqft (e.g. 2,700)
- Max year built (e.g. 1975)
- Min/max living sqft (e.g. 1,200 / 1,600)
- City + optional ZIP  
and show **count** and optionally a table of candidate parcels (or a “Target pipeline” summary that uses the same filters).

---

## 2. Lot dimensions and buildable footprint (40 ft vs 50 ft wide, 100–120 ft deep, setbacks)

**Ask:** Need to know if we need **40 ft vs 50 ft wide**, **100–120 ft deep**, and **setbacks**. Every property should have a **buildable footprint** from zoning (e.g. 60×100 lot, 10 ft side / 20 ft front–rear → 50×60 buildable).

**In codebase:**
- **Buildable footprint** is implemented in **`_buildable_footprint_from_zoning()`** in `queries.py`:
  - Uses **`_ZONE_LOOKUP`** (R1, R2, RS, RE, RM) with **front_setback_ft**, **rear_setback_ft**, **side_setback_ft** (e.g. 20/20/5 for R1).
  - Formula: buildable width = lot_width − 2×side; buildable depth = lot_depth − front − rear.
- **Rebuild eval** returns **`buildable_footprint`**: `buildable_width_ft`, `buildable_depth_ft`, `buildable_sq_ft`, `notes`.
- **Site search** can filter by **`min_width_ft`**, **`min_depth_ft`** so you only get e.g. “at least 50 ft wide” buildable.

**In UI:**
- **Rebuild** tab: after running rebuild eval, section **“Buildable footprint (lot minus setbacks)”** shows **buildable_width_ft**, **buildable_depth_ft**, **buildable_sq_ft** and notes.
- There is **no** UI to filter or aggregate by “40 ft vs 50 ft wide” or “100–120 ft deep” across many parcels; that would be a site-search with `min_width_ft` / `min_depth_ft` (and possibly a summary by width/depth band).

**Suggested next step:** In any new “Site search / Target pipeline” card, expose **min buildable width** and **min buildable depth** (or lot width/depth) so Robert can ask “50 ft wide, 100 ft deep” type queries.

---

## 3. AVM for “buy it now” and acquisition box

**Ask:** AVM value is good for **existing value**; comfortable using it for “buy it now” price. That value + **footprint + zoning** = **acquisition box**.

**In codebase:**
- **Existing value** in rebuild eval uses **MLS** `sold_price` when available; when missing, we use **Attom** `suggested_existing_value` (AVM or last sale) and set **`existing_value_source`** to `"attom"` or `"mls"`.
- **Footprint** = parcel footprint + **buildable footprint** (lot minus setbacks).
- **Zoning** = zone_code, max_gfa_estimate, etc. from **zoning_summary**.

**In UI:**
- **Rebuild** tab: after run, you see **Existing value** (with “mls” or “attom” in parentheses), **Parcel footprint**, **Buildable footprint**, **Zoning**, and **Comps economics**. Together that is the “acquisition box” (value + footprint + zoning).

**Suggested next step:** Optionally label that block in the UI as “Acquisition box” (existing value + buildable footprint + zoning) so it’s explicit.

---

## 4. Product value on every lot (2,700 sq ft): would it sell, would it fit, aggregate value created

**Ask:** For product = **2,700 sq ft**: what would it **sell for on every lot** in the DB? **Could it fit?** What is **aggregate value created**?

**In codebase:**
- **`target_pipeline_summary()`** does exactly this:
  - Uses **site_search** (same filters: target_sqft, city, ZIP, max_year_built, min/max_living_sq_ft, zone_codes) to get qualifying parcels.
  - For each parcel: **existing value** from latest sale; **new-build value** from **new_build_benchmark** (per ZIP) × target_sqft.
  - Returns **parcel_count**, **total_existing_value**, **total_new_build_value**, **total_value_created**.
- **API:** **`POST /decisions/target-pipeline-summary`** is now exposed (same params: target_sqft, city_name, zip_code, max_year_built, min/max_living_sq_ft, limit).

**In UI:** **Rebuild** tab → **“Target pipeline (aggregate value)”** card: target sqft (default 2,700), optional max year built (e.g. 1975), min/max living sq ft (e.g. 1,200 / 1,600), ZIP, limit → **Get summary** shows parcel count, total value created, total existing/new-build value, parcels_with_sale, zips_with_benchmark.

---

## 5. Optimum product mix (2,100 vs 2,700 vs 3,500)

**Ask:** What product gives **optimum mix of quantity and value**? 3,500 sq ft = more profit per unit, fewer properties; 2,100 sq ft = fits 90% but may only create $100k value vs $700k build cost.

**In codebase:**
- **Single-product** summary exists: **target_pipeline_summary** for one **target_sqft**.
- There is **no** multi-product comparison (e.g. run for 2,100, 2,700, 3,500 and compare count vs total value vs build cost).

**In UI:** No comparison view.

**Suggested next step:**  
- Add an API or a loop that runs **target_pipeline_summary** for several **target_sqft** values (e.g. 2,100, 2,700, 3,500).  
- Add a **“Product mix”** card: same filters (city, ZIP, 50 yr old, ~1,400 sq ft), then a table or chart: for each product size, show **parcel count**, **total value created**, and (if build cost is input) **value created vs build cost** or margin, so Robert can see the tradeoff.

---

## 6. Baseline heat map of 2,700 sq ft sell price; subtract AVM = value accretion

**Ask:** **Baseline heat map** of what a **2,700 sq ft home would sell for** in a region; **subtract existing AVM** from that heat map value → **estimated value accretion**. Don’t need unique comp per property; neighbors can share same heat map value.

**In codebase:**
- **Grid/ZIP PPSF** exists: e.g. **`mv_agg_grid_year_ppsf_025`** (grid × year median PPSF), **new_build_benchmark** (ZIP × year new-build PPSF).
- “Sell price for 2,700 sq ft” = **PPSF × 2,700** at grid or ZIP level.
- **Value accretion** = that sell price − **existing value** (AVM or sale). Existing value is per parcel (MLS or Attom); at “every lot” scale we’d need either Attom in bulk or our existing **latest sale** per parcel (which we have in target_pipeline_summary).

**In UI:**
- **Rebuild** and **region** tabs have **heatmaps** (lot size, home size, home×lot) and **new-build benchmark**.
- There is **no** dedicated “heat map of new-build value (e.g. 2,700 × PPSF)” and **no** “value accretion heat map” (heat map value − existing value).

**Suggested next step:**  
- Define a **“new-build value”** layer: e.g. per grid cell (or ZIP), **median_new_build_ppsf × 2,700** (or target_sqft parameter).  
- Optionally a **“value accretion”** view: for parcels in a region, use that heat map value at the parcel’s cell/ZIP minus parcel’s existing value (from latest sale or, where we have it, Attom AVM).  
- Expose in API and/or as a new heat map type in the UI (“Expected sell price for 2,700 sq ft” and “Value accretion vs heat map”).

---

## Summary: where to find things today

| Robert ask | Where it lives | Find it in UI? |
|------------|----------------|----------------|
| Buildable footprint (60×100 → 50×60, setbacks) | Rebuild eval, buildable_footprint section | **Yes** – Rebuild tab, after run: “Buildable footprint” |
| AVM as existing value / acquisition box | Rebuild eval, comps_economics.existing_value (Attom fallback) | **Yes** – Rebuild tab, “Existing value (attom)” or “(mls)” |
| Parcels that fit 2,700, 50 yr old, ~1,400 sq ft | site_search() with max_year_built, min/max_living_sq_ft | **No** – API only: POST /decisions/site-search |
| Aggregate value created for 2,700 sq ft | target_pipeline_summary(); POST /decisions/target-pipeline-summary | **Yes** – Rebuild tab, “Target pipeline (aggregate value)” card |
| Lot width/depth and setback filters | site_search min_width_ft, min_depth_ft; _ZONE_LOOKUP setbacks | **Partially** – buildable footprint visible per parcel; no bulk “40 ft vs 50 ft” view |
| Heat map of 2,700 sq ft sell price; value accretion | Would need PPSF × 2,700 by grid/ZIP; then − AVM | **No** – heat maps exist for lot/home size; no “value” or “accretion” heat map |

---

## Recommended next steps (priority)

1. **Expose target pipeline in API + UI** ✅ **Done.**  
   - **`POST /decisions/target-pipeline-summary`** added.  
   - **“Target pipeline (aggregate value)”** card on Rebuild tab: target sqft, max year built, min/max living sq ft, ZIP, limit → **Get summary** shows parcel count, total value created, total existing/new-build, parcels_with_sale, zips_with_benchmark.

2. **Optional: Site search card**  
   - Same filters as above, show **list or count** of candidate parcels (and optionally min width/depth so he can ask “50 ft wide, 100 ft deep”).

3. **Optional: Product mix comparison**  
   - Run target-pipeline summary for 2,100, 2,700, 3,500 (same filters) and show table/chart: count vs value created so he can see optimum mix.

4. **Optional: Value heat map**  
   - “Expected sell price for 2,700 sq ft” by grid or ZIP (PPSF × 2,700); then “value accretion” = that − existing value where existing value is available.

5. **Optional: Label “Acquisition box”** in Rebuild tab for existing value + buildable footprint + zoning.
