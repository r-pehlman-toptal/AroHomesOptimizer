# Attom APIs suitable for implementing Aro homes–style features

This doc maps each **Aro homes (my data)** feature to **Attom API endpoints** that can provide equivalent or complementary data. Use it to implement Attom-backed versions of the same flows (e.g. under the Attom tab or for areas where Aro DB has no coverage).

---

## Summary table

| Aro feature | Data Aro uses | Suitable Attom API(s) | Notes |
|-------------|---------------|----------------------|--------|
| **Property details (single)** | — | `/property/detail?address=`, `/attomavm/detail?attomId=`, `/saleshistory/*` | Already implemented. |
| **Existing value (AVM)** | MLS sold_price or Attom fallback | `/property/detail` (includes AVM), `/attomavm/detail` (by address, attomId, **postalCode**, or **lat/long+radius**) | Single: address/attomId. Bulk: **/attomavm/detail** with postalCode or radius. |
| **Site search** (parcels where target fits, 50 yr old, ~1,400 sq ft) | Parcel + zoning + lot + year/size from sales | **/property/snapshot** or **/property/detail** with **postalCode** or **lat/long+radius** + **minYearBuilt**, **minUniversalSize**, **maxUniversalSize**, **minLotSize2** | No zoning/setbacks in Attom; use lot size + improvement size as proxy for “fits target”. |
| **Target pipeline (aggregate value)** | Site search + latest sale + new-build benchmark | **/attomavm/detail** with **postalCode** (or radius) + **minYearBuilt**, **minUniversalSize**, **maxUniversalSize** → list of properties with AVM; aggregate in app. New-build value: use **/salestrend/snapshot** or **/transaction/salestrend** (median/avg sale price by area) or AVM × target sqft. | One call per ZIP (or radius); compute value created in backend. |
| **Rebuild eval** (footprint, zoning, feasibility, comps) | Parcel, zoning, buildable footprint, comps, existing value | **/property/detail** (lot, improvement, AVM, sale); **/attomavm/detail** (AVM). **No zoning/setbacks** in Attom → no true “buildable footprint”; use lot + improvement size only. Comps: **/sale/snapshot** or **/sale/detail** with same postalCode/radius. | Attom can do “value + lot + improvement”; buildable footprint and feasibility stay Aro-only or heuristic. |
| **Feasibility** (does target sqft fit?) | Zoning + lot dimensions + setbacks | Attom has **lot size**, **improvement size** (universalSize). No zoning/setbacks → only “does lot fit target sqft?” (e.g. lot_sq_ft ≥ target), no setback-based buildable area. | Yes (estimated from lot area + assumed setbacks; no zoning). |
| **New-build benchmark** (PPSF by area) | DB: median new-build PPSF by ZIP/year | **/salestrend/snapshot** or **/transaction/salestrend** by **geoIdV4** (ZIP/area): **medSalePrice**, **avgSalePrice**, **homeSaleCount** by interval. Filter by property type if needed. | Area-level median/avg sale price; not necessarily “new build” unless Attom exposes build year/type. |
| **Comps / market (region)** | Comps by ZIP, counts, medians | **/sale/snapshot** or **/sale/detail** with **postalCode** or **lat/long+radius**; **/salestrend/snapshot** for trend (median/avg, counts). | Comps = sale list in area; trend = aggregated. |
| **Product areas** (where to build) | Rank areas by PPSF, DOM, supply | **/attomavm/detail** or **/property/snapshot** by **postalCode** (multiple ZIPs) or **GEOIDV4**; **/salestrend/snapshot** for median/avg by area. Aggregate by ZIP in app and rank. | Area API **geoIdV4** + Property/AVM/Sale endpoints by geography. |
| **Portfolio rank** (rank parcels by feasibility + margin) | Per-parcel feasibility + economics | Per-address: **/property/detail** + **/attomavm/detail** for each; or **/attomavm/detail** with **postalCode**/radius to get many, then filter to your list. | Bulk by ZIP/radius; or loop addresses (small lists only). |
| **Heat maps** (lot size, home size) | Parcel-level lot_sq_ft, living_sq_ft, year_built | **/property/snapshot** with **postalCode** or **lat/long+radius** + **minLotSize2**, **maxLotSize2**, **minUniversalSize**, **maxUniversalSize**, **minYearBuilt**, **maxYearBuilt**. Paginate or use response list to bucket into heat map. | Build buckets in app from property list. |
| **Sales history** | — | **/saleshistory/snapshot** or **/saleshistory/detail** (by address or attomId). Single property per request. | Already used in Property details. |
| **Assessment / tax** | — | **/assessment/detail** or **/assessment/snapshot** (by address, attomId, **postalCode**, or **lat/long+radius**). | Single or area. |

---

## Recommended Attom endpoints by use case

### 1. Single-property (already in use)

- **Property detail**: `GET /property/detail?address={encoded}`  
  → address, beds, baths, living_sq_ft, lot_sq_ft, year_built, AVM, last sale, assessment.
- **AVM when missing**: `GET /attomavm/detail?attomId={id}`.
- **Sale history**: `GET /saleshistory/snapshot` or `/saleshistory/detail` (by address or attomId).

### 2. Area / “pipeline” (multi-property in one call)

- **List properties in ZIP with filters (e.g. 50+ yr, ~1,200–1,600 sq ft)**  
  `GET /property/snapshot?postalCode={zip}&minYearBuilt=1975&minUniversalSize=1200&maxUniversalSize=1600`  
  Optional: `minLotSize2`, `maxLotSize2`, `propertyType`, etc.
- **AVM for all those properties in one call**  
  `GET /attomavm/detail?postalCode={zip}&minYearBuilt=1975&minUniversalSize=1200&maxUniversalSize=1600`  
  → Returns list of properties with AVM; aggregate in app for “target pipeline” (value created = new-build value − AVM).
- **Sales in area (comps)**  
  `GET /sale/snapshot?postalCode={zip}` or with **latitude, longitude, radius**; optional filters (minSaleAmt, minYearBuilt, etc.).
- **Median / average sale price by area (benchmark)**  
  **/salestrend/snapshot** (geoID or geoIDV4, interval, year range) → **medSalePrice**, **avgSalePrice**, **homeSaleCount**.  
  Or **/transaction/salestrend** (geoIdV4, interval, start/end year) → same.
- **Assessments/taxes by area**  
  `GET /assessment/snapshot?postalCode={zip}` or lat/long+radius.

### 3. Geography (Area API)

- **Resolve area to geoIdV4** (for use in Property/AVM/Sale/SalesTrend by geography):  
  Area API **Location Lookup**, **Hierarchy Lookup**.
- Then call Property API with **geoIDV4=** (multi-value) to query by neighborhood, county, etc.

---

## Gaps (Attom cannot replace Aro)

| Capability | Why Attom doesn’t cover it |
|------------|----------------------------|
| **Zoning (zone code, setbacks, max GFA)** | Attom does not expose zoning or setback rules. |
| **Buildable footprint** (lot minus setbacks) | **We can estimate it**: from Attom **lot_sq_ft** only we assume depth ≈ 2× width and apply default setbacks (20/20/5 ft) → **buildable_width_ft**, **buildable_depth_ft**, **buildable_sq_ft**. No zoning, so notes say "assumed setbacks (no zoning)". |
| **Feasibility (pass/fail by zoning + footprint)** | Requires zoning + buildable footprint. |
| **Aro parcel ID / internal property_id** | Attom uses attomId, address, FIPS+APN; no link to Aro DB unless you maintain a mapping. |
| **New-build-only benchmark** | Attom sales trend is all sales in area; filtering to “new build” would require build year or similar in response. |

So: **existing value (AVM), lot/improvement size, sales history, comps list, area median sale price** → Attom can support. **Buildable footprint and “fits target”** can be **calculated** from Attom lot_sq_ft (estimated dimensions + assumed setbacks 20/20/5 ft); see `estimate_buildable_footprint()` and rebuild-features fields **buildable_***, **fits_target_sqft**. **Zoning** (true setbacks, FAR) → stay on Aro (or add another zoning source).

---

## Reference

- Attom API docs: https://api.developer.attomdata.com/docs  
- Area/list params: **POSTALCODE**, **latitude + longitude + radius**, **minYearBuilt**, **maxYearBuilt**, **minUniversalSize**, **maxUniversalSize**, **minLotSize2**, **maxLotSize2**, **propertyType**, **geoIDV4**.  
- Current client: `src/attom/client.py` (property/detail, attomavm/detail by attomId, avm/snapshot by lat/long+radius, sale history).
