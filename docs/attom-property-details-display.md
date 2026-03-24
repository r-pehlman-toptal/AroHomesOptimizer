# Property details you can display (Attom API)

From the Attom Property API response (e.g. `/property/detail`), you can display the following. Our client normalizes many of these for the UI and rebuild features.

---

## What you see in the Attom tab (UI)

In **Attom** → **Property details**, after **Look up** by address:

| Section | Attom data shown |
|--------|-------------------|
| **Header** | One-line address |
| **Value block** | AVM (estimated value) or last sale amount |
| **Stats row** | Beds, Baths, Sq ft, Year built, Lot size (sq ft) |
| **Hero line** | Beds · baths · sqft · lot · year built · property type |
| **PPSF / rent** | $/sqft and estimated monthly rent (when value + sqft) |
| **Home value** | AVM with confidence, range (high/low), $/sqft; or last sale |
| **Facts & features (table)** | Address, City/State/ZIP, Bedrooms, Bathrooms, Livable area, Lot size, Year built, Property type, Assessed value, Tax amount (year), Market value, Est. value per sqft, **Lot depth (ft)**, **Lot width / frontage (ft)**, **Latitude**, **Longitude**, Attom ID |
| **Price history** | Sale history (date, event, price, $/sqft) – loaded async |
| **Rebuild eval (Attom)** | **Run rebuild eval** (target sqft + address): **Feasibility** (Pass/Fail from fits_target_sqft), **Buildable footprint** (width × depth, sqft, notes), **Existing value**, **Value accretion** (est. new build − existing), plus details table. Attom-only; no Aro DB. |

---

## Identifier

| Field | Attom path | Display |
|-------|------------|--------|
| **obPropId** | `identifier.obPropId` | Internal Attom property ID |
| **FIPS** | `identifier.fips` | County FIPS code (e.g. 10001) |
| **APN** | `identifier.apn` | Assessor parcel number |
| **APN (original)** | `identifier.apnOrig` | Original APN format |

---

## Lot

| Field | Attom path | Normalized in client | Display |
|-------|------------|----------------------|--------|
| **Lot depth (ft)** | `lot.depth` | `lot_depth_ft` | Yes (when present) |
| **Lot frontage / width (ft)** | `lot.frontage` | `lot_width_ft` | Yes (when present) |
| **Lot size (acres)** | `lot.lotsize1` | — | Optional |
| **Lot size (sq ft)** | `lot.lotsize2` | `lot_sq_ft` | Yes |
| **Lot number** | `lot.lotnum` | — | Optional |

When **depth** and **frontage** are present, we use them for **buildable footprint** (with assumed setbacks) and **fits_target_sqft**; otherwise we estimate dimensions from lot area.

---

## Address

| Field | Attom path | Display |
|-------|------------|--------|
| **One-line address** | `address.oneLine` | Primary display |
| **Line 1** | `address.line1` | Street |
| **Line 2** | `address.line2` | City, state, ZIP |
| **Locality** | `address.locality` | City |
| **State** | `address.countrySubd` | State (e.g. DE) |
| **ZIP** | `address.postal1` | Postal code |

---

## Location

| Field | Attom path | Display |
|-------|------------|--------|
| **Latitude** | `location.latitude` | Yes (geocode / map) |
| **Longitude** | `location.longitude` | Yes |
| **Accuracy** | `location.accuracy` | e.g. "Street" |
| **GeoID** | `location.geoid` | Area IDs (county, place, ZIP, etc.) |

---

## Summary (property class / type)

| Field | Attom path | Display |
|-------|------------|--------|
| **Property class** | `summary.propclass` | e.g. Apartment |
| **Subtype** | `summary.propsubtype` | e.g. SINGLE FAMILY |
| **Property type** | `summary.proptype` | e.g. APARTMENT |
| **Year built** | `summary.yearbuilt` | Yes |
| **Land use** | `summary.propLandUse` | Optional |
| **Legal description** | `summary.legal1` | Optional |
| **Owner occupied** | `summary.absenteeInd` | OWNER OCCUPIED / Absentee |

---

## Building – size

| Field | Attom path | Normalized | Display |
|-------|------------|------------|--------|
| **Living size (sq ft)** | `building.size.livingsize` | `living_sq_ft` | Yes |
| **Universal size** | `building.size.universalsize` | Used when livingsize missing | Yes |
| **Building size** | `building.size.bldgsize` | — | Optional |
| **Basement size** | `building.interior.bsmtsize` | — | Optional |
| **Basement type** | `building.interior.bsmttype` | — | Optional |

---

## Building – rooms

| Field | Attom path | Display |
|-------|------------|--------|
| **Beds** | `building.rooms.beds` | Yes |
| **Baths total** | `building.rooms.bathstotal` | Yes |
| **Baths full** | `building.rooms.bathsfull` | Optional |
| **Baths half** | `building.rooms.bathshalf` | Optional |
| **Total rooms** | `building.rooms.roomsTotal` | Optional |

---

## Building – summary / construction

| Field | Attom path | Display |
|-------|------------|--------|
| **Levels / stories** | `building.summary.levels` | Optional |
| **Building type** | `building.summary.bldgType` | e.g. SINGLE FAMILY |
| **Condition** | `building.construction.condition` | e.g. GOOD |
| **Wall type** | `building.construction.wallType` | Optional |
| **Heating** | `utilities.heatingtype` | Optional |
| **Cooling** | `utilities.coolingtype` | Optional |

---

## Area (jurisdiction)

| Field | Attom path | Display |
|-------|------------|--------|
| **County** | `area.countrysecsubd` | e.g. Kent County |
| **Municipality** | `area.munname` | e.g. DUCK CREEK |
| **Subdivision** | `area.subdname` | e.g. WOODLAND MANOR PH I |

---

## Valuation / AVM / Sale (when present)

| Field | Source | Display |
|-------|--------|--------|
| **AVM value** | `valuation.avm` or `/attomavm/detail` | Yes |
| **AVM high/low** | `valuation.amount.high/low` | Optional |
| **Confidence (scr)** | `valuation.scr` | Optional |
| **Last sale amount** | `sale.amount` or salehistory | Yes |
| **Last sale date** | `sale.saleTransDate` | Yes |
| **Assessed value** | `assessment.assessed.assdttlvalue` | Yes |
| **Tax amount** | `assessment.tax.taxamt` | Yes |
| **Tax year** | `assessment.tax.taxyear` | Yes |
| **Market value** | `assessment.market.mktttlvalue` | Optional |

---

## Calculated / derived (our client)

| Field | Description |
|-------|-------------|
| **buildable_width_ft** | Lot width minus 2× side setback (from lot.frontage/depth or estimated) |
| **buildable_depth_ft** | Lot depth minus front and rear setbacks |
| **buildable_sq_ft** | Buildable pad area (assumed setbacks when no zoning) |
| **fits_target_sqft** | True if buildable_sq_ft ≥ target when target sqft given |
| **suggested_existing_value** | AVM or last sale (for rebuild “acquisition box”) |
| **value_per_sqft** | AVM / living_sq_ft or from API |

---

## Vintage (optional)

| Field | Attom path | Display |
|-------|------------|--------|
| **Last modified** | `vintage.lastModified` | Optional |
| **Publication date** | `vintage.pubDate` | Optional |

---

In short: you can show **identifier** (APN, FIPS), **address**, **lot** (depth, frontage, lotsize2), **location** (lat/long), **summary** (type, year built, owner), **building** (beds, baths, livingsize, levels, condition), **area** (county, mun, subdivision), **valuation/sale/assessment**, and our **calculated** buildable footprint and fits_target when a target sqft is set. When Attom returns **lot.depth** and **lot.frontage**, we use them for buildable footprint instead of estimating from area.
