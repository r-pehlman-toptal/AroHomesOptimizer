# Rebuild evaluation API

`POST /queries/rebuild-eval` evaluates a parcel for rebuild: it resolves the given address to a `property_id`, then returns property info, parcel footprint, zoning summary, feasibility (max GFA vs target sqft), and comps economics (PPSF percentiles and price band). No external APIs are used; all data comes from the DB and existing query_service patterns.

## Request

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `address_text` | string | yes | — | Address string or numeric `property_id`. |
| `target_living_sq_ft` | float | no | 2700 | Target living sqft for feasibility and comps. |
| `size_band_pct` | float | no | 0.2 | Comps size band ±pct around target (e.g. ±20%). |
| `comps_recency_months` | int | no | 12 | Only comps sold in last N months. |
| `min_year_built` | int | no | null | Optional (not yet applied in comps). |
| `zip_code` | string | no | null | Optional; narrows address lookup when `address_text` is not numeric. |
| `city_name` | string | no | null | Optional; narrows address lookup. |

Example:

```json
{
  "address_text": "12345",
  "target_living_sq_ft": 2700,
  "size_band_pct": 0.2,
  "comps_recency_months": 12
}
```

## Response

- **property_id** — Resolved parcel ID; `null` if address could not be resolved.
- **resolved_address** — Human-readable address (e.g. "Property 12345, 90210, LOS ANGELES").
- **is_valid** — `true` when the response has usable parcel geometry or zoning; `false` when address is unresolved or both geometry and zoning are missing.
- **notes** — Set when `is_valid` is false (e.g. "Missing parcel geometry or zoning data.").
- **property_info** — Latest MLS sale for the property (optional).
- **parcel_footprint** — Lot width, depth, ratio_band, `is_valid_dimensions` (optional).
- **zoning_summary** — Zone, `lot_size_sq_ft`, `max_gfa_estimate`, etc. (optional).
- **buildable_footprint** — Buildable pad from lot minus zone setbacks (optional). See below.
- **feasibility_fit** — See below.
- **comps_economics** — See below.
- **f3_offer_range** / **f4_overpay_risk** — Optional; currently not populated.

### buildable_footprint

- **buildable_width_ft** = lot width − 2 × side setback; **buildable_depth_ft** = lot depth − front − rear setback (from zone lookup; default 20/20/5 ft when zone unknown).
- **buildable_sq_ft** = buildable_width_ft × buildable_depth_ft. Set to `null` when setbacks exceed lot dimensions; **notes** may explain (e.g. "Setbacks exceed lot dimensions; no buildable pad.").

### fits_target_sq_ft

- **max_gfa_estimate** comes from `zoning_summary` (zone lookup: FAR × lot area or table value).
- **fits_target_sq_ft** is `true` when `max_gfa_estimate` is set and `max_gfa_estimate >= target_living_sq_ft`; otherwise `false`.
- **fit_notes** explains when max GFA is missing or when target exceeds max GFA.

### Confidence (comps_economics)

- **confidence_band** and **confidence_score** come from the comps aggregate: coverage (comp_count/30), proximity (distance half-life), recency (time half-life), and tightness (IQR vs median PPSF). See `comps_confidence.confidence_score_and_band`.
- **comp_count**, **median_dist_miles**, **median_months_ago**, and **hint** (e.g. when subject has no geometry) are returned for diagnostics.

## Example response (success)

```json
{
  "property_id": 12345,
  "resolved_address": "Property 12345, 90210, LOS ANGELES",
  "is_valid": true,
  "notes": null,
  "property_info": { "sale_id": 1, "property_id": 12345, "sold_date": "2023-06-01", "sold_price": 2100000, "living_sq_ft": 2500, "ppsf": 840, "zip_code": "90210", "city_name": "LOS ANGELES" },
  "parcel_footprint": { "property_id": 12345, "lot_size_sq_ft": 7500, "lot_width_ft": 60, "lot_depth_ft": 125, "ratio_band": "moderate", "is_valid_dimensions": true },
  "zoning_summary": { "parcel_id": 12345, "zone_code": "LAR1", "lot_size_sq_ft": 7500, "max_gfa_estimate": 3750 },
  "buildable_footprint": { "buildable_width_ft": 50, "buildable_depth_ft": 85, "buildable_sq_ft": 4250, "notes": null },
  "feasibility_fit": { "max_gfa_estimate": 3750, "fits_target_sq_ft": true, "fit_notes": null },
  "comps_economics": { "p25_ppsf": 800, "p50_ppsf": 850, "p75_ppsf": 920, "price_low": 2160000, "price_base": 2295000, "price_high": 2484000, "comp_count": 42, "confidence_band": "high", "confidence_score": 0.78, "median_dist_miles": 0.3, "median_months_ago": 4.2, "hint": null },
  "f3_offer_range": null,
  "f4_overpay_risk": null
}
```

## Example response (missing data)

When geometry or zoning is missing, `is_valid` is false and `notes` is set:

```json
{
  "property_id": 99999,
  "resolved_address": "Property 99999, 90210, LOS ANGELES",
  "is_valid": false,
  "notes": "Missing parcel geometry or zoning data.",
  "property_info": null,
  "parcel_footprint": null,
  "zoning_summary": null,
  "feasibility_fit": { "max_gfa_estimate": null, "fits_target_sq_ft": false, "fit_notes": "No max GFA from zoning." },
  "comps_economics": { "comp_count": 0, "confidence_band": "low", "hint": "Subject property has no location in property_geometry..." },
  "f3_offer_range": null,
  "f4_overpay_risk": null
}
```
