# How much – aggregate (comps with filters, weights, confidence)

## Summary

- **Row-level:** Build a comp set with hard filters and a per-comp weight `w = recency_weight * proximity_weight`.
- **Group-level:** From that set, compute comp_count, median_ppsf, p25/p75, iqr, median_dom, and similarity diagnostics.
- **Confidence:** Score from four signals (coverage, proximity, recency, tightness); map to band High / Medium / Low.
- **Volume:** Per ZIP × month or ZIP × year: sale_count, median_ppsf, median_dom for liquidity/trends.

## Delivered

| Item | Location |
|------|----------|
| **Aggregate SQL** | `sql/readonly/comps_aggregate.sql` – subject_parcel_id, subject_sqft, filters, weights, one aggregate row |
| **Rows SQL** | `sql/readonly/comps_aggregate_rows.sql` – same filters, returns comp rows with dist_miles, months_ago, w |
| **Confidence** | `src/query_service/comps_confidence.py` – confidence_score_and_band() from coverage, proximity, recency, tightness |
| **Schemas** | `CompsAggregateParams`, `CompsAggregateRow`, `CompsAggregateCompRow` in `src/query_service/schemas.py` |
| **Queries** | `comps_aggregate()`, `comps_aggregate_rows()` in `src/query_service/queries.py` |
| **Endpoints** | `POST /queries/comps-aggregate`, `POST /queries/comps-aggregate-rows` |
| **Volume SQL** | `sql/readonly/volume_by_zip_year.sql`, `volume_by_zip_month.sql` (no API yet; use for Tableau/liquidity) |

## Hard filters (comps set)

- Same **property_subtype** (property_use_standardized), optional (None = no filter).
- **sold_date** >= now − **recency_months** (default 12).
- **living_sq_ft > 0**, **sold_price > 0**.
- Optional **size band:** living_sq_ft between subject_sqft × (1 − size_band_pct) and subject_sqft × (1 + size_band_pct) (default ±20%).
- Optional **distance cap:** ST_DWithin(subject_point_3310, comp_point_3310, distance_cap_miles) (default 2 miles).
- **ppsf_min** (default 400).
- LA only (city name), exclude subject parcel.

## Soft scoring (weight per comp)

- **recency_weight** = exp(−months_ago / half_life_months), default half-life 6 months.
- **proximity_weight** = exp(−dist_miles / half_life_miles), default half-life 0.5 miles.
- **w** = recency_weight × proximity_weight (size can be added later as a third factor).

## Group-level aggregates

- **Market/value:** comp_count, median_ppsf, p25_ppsf, p75_ppsf, iqr_ppsf.
- **Liquidity:** median_dom, p75_dom.
- **Similarity diagnostics:** pct_within_025mi, pct_within_05mi, pct_within_3mo, pct_within_6mo, pct_within_20pct_sqft.

## Confidence score and band

- **coverage** = min(1, comp_count / 30).
- **proximity** = exp(−median_dist_miles / 0.5).
- **recency** = exp(−median_months_ago / 6).
- **tightness** = 1 − min(1, iqr_ppsf / median_ppsf).
- **score** = 0.35×coverage + 0.25×proximity + 0.25×recency + 0.15×tightness (0–1).
- **Band:** ≥ 0.75 High, ≥ 0.55 Medium, else Low.

## Volume (liquidity / trend)

- **volume_by_zip_year.sql:** GROUP BY zip_code, sale_year → sale_count, median_ppsf, median_dom. Params: min_sold_date, optional zip_code.
- **volume_by_zip_month.sql:** GROUP BY zip_code, sale_month → sale_count, median_ppsf, median_dom. Params: min_sold_date, optional zip_code.

Use for “selling numbers” per month/year/ZIP; no API yet—run directly or add endpoints later.

## References

- Data map: `docs/data-map.md` (property_geometry for point_3310, mls_history for sold_date, days_on_market, property_use_standardized).
- Conventions: `docs/features/CONVENTIONS.md` (no duplicate endpoints; derive from existing when possible).
