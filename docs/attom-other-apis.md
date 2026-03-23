# Attom: Other APIs (bulk / area-based)

Attom has several APIs beyond single-property-by-address that we could use for area-level or “pipeline-style” flows.

---

## 1. Property API – area / list endpoints (multi-property per request)

Many Property API endpoints accept **geography** and return **multiple properties** in one call (no per-address loop):

| Endpoint | Geography params | Filters (examples) | Use case |
|----------|------------------|--------------------|----------|
| **/property/snapshot** | `postalCode`, or `latitude` + `longitude` + `radius` | `minYearBuilt`, `maxYearBuilt`, `minUniversalSize`, `maxUniversalSize`, `minLotSize2`, `propertyType` | List properties in a ZIP or radius with filters (e.g. 50+ years old, 1,200–1,600 sq ft). |
| **/attomavm/detail** | `postalCode`, or `latitude` + `longitude` + `radius` | Same + `minAVMValue`, `maxAVMValue` | **AVM for many properties in one call** (ZIP or radius). |
| **/sale/snapshot** | `postalCode`, or lat/long + `radius` | `minSaleAmt`, `maxSaleAmt`, `minUniversalSize`, `minYearBuilt`, etc. | Recent sales in area with filters. |
| **/sale/detail** | Same | Same | Sale detail for area. |
| **/assessment/detail**, **/assessment/snapshot** | `postalCode`, or lat/long + radius | — | Assessments/taxes by area. |

So:

- **Target-pipeline-style with Attom**: Call **/attomavm/detail** (or **/property/snapshot**) with e.g. `postalCode=91207`, `minYearBuilt=1975`, `minUniversalSize=1200`, `maxUniversalSize=1600` to get **all matching properties in that ZIP with AVM** in one (or few) request(s). Then aggregate value created (e.g. new-build PPSF × target sqft − AVM) in your app. No need to call by address for each parcel.
- We already use **/avm/snapshot** with lat/long + radius for “AVM in radius” (see `fetch_avm_in_radius` in `src/attom/client.py`). **/attomavm/detail** with `postalCode` or radius is the same idea with more filters (year built, size, etc.).

Ref: [ATTOM API Documentation](https://api.developer.attomdata.com/docs) → Property API → Search Filters (POSTALCODE, RADIUS, LONGITUDE & LATITUDE, YEARBUILT, UNIVERSALSIZE, etc.).

---

## 2. Area API (separate product)

- **Location Lookup**, **Hierarchy Lookup**, **Boundary** definitions.
- Uses **geoIdV4** (Attom’s geographic IDs) for areas (county, ZIP, school district, neighborhood, etc.).
- Property API endpoints can be queried by **GEOIDV4** (multi-value) so you can run area-level queries by Attom’s own geography, not only by postal code or lat/long.

Ref: [ATTOM API Documentation](https://api.developer.attomdata.com/docs) → Area API.

---

## 3. Bulk data delivery (not REST API)

- **Bulk data**: CSV files delivered via **FTP** (weekly/monthly/quarterly/annual).
- Use when you need to store data longer than the 24-hour API cache, or analyze very large datasets without many API calls.
- Products include: Schools, Home Sale Trends, Boundaries, Community, Transit. Custom bulk solutions via [contact with Attom](https://api.developer.attomdata.com/home#ContactAttom).

Ref: [ATTOM Developer Platform – Bulk](https://api.developer.attomdata.com/bulk).

---

## Summary: “Can we use Attom for target pipeline?”

- **Yes, in an area-based way**: Use **/attomavm/detail** (or **/property/snapshot**) with **postalCode** or **latitude + longitude + radius**, plus **minYearBuilt**, **minUniversalSize**, **maxUniversalSize**, etc., to get many properties with AVM in one call. Then compute “value created” (e.g. new-build value − AVM) and aggregate in your backend. No per-address loop.
- **Current target pipeline** stays on Aro DB (parcels, zoning, sales, new-build benchmark) for scale and one source of truth. An **optional “Attom target pipeline”** could be added for a **single ZIP or radius**: one Attom call → list of properties + AVM → aggregate value created for a target sqft (using your or Attom’s new-build value logic).
