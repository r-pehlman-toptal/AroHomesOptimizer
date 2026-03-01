# Data quality memo – Gold layer and backbone

**Scope:** parcel_gold, transaction_gold, and upstream tables (property_address, mls_history, property_geometry).  
**Purpose:** Document 2–3 principal risks for handoff to feasibility and modeling (Week 3+).

---

## 1. Nulls and coverage

- **Geometry:** Many parcels may have no row in `property_geometry` or NULL `center_point`. parcel_gold LEFT JOINs geometry, so `center_point_4326` and `lot_size_sq_ft` will be NULL for those. Grid-based and spatial analyses will exclude or impute these; document % with geometry in profiling.
- **year_built:** Sourced from latest MLS sale per property. Parcels with no sale, or sales with NULL `year_built`, will have NULL in parcel_gold. Feasibility and modeling should treat NULL explicitly (e.g. exclude or use submarket default).
- **days_on_market / baths:** transaction_gold uses `days_on_market` and derived `baths` (bathrooms_full + 0.5 * bathrooms_half). Nulls in MLS will propagate; city_year and other aggregates should use COUNT of non-null or document exclusion.

**Recommendation:** Profile null rates per key column (parcel_gold: center_point_4326, year_built; transaction_gold: days_on_market, baths). Add a small profiling script or notebook if needed.

---

## 2. Duplication and referential consistency

- **One address per parcel:** parcel_gold uses DISTINCT ON (property_id) on property_address. If multiple addresses exist per property, only one is chosen (min street_id). Downstream should not assume “primary” address without business rules.
- **Transaction–parcel link:** transaction_gold is built from mls_history only. If some mls_history.property_id do not appear in property_address, those rows will have no matching parcel_gold.parcel_id. Referential check: `transaction_gold.parcel_id` IN parcel_gold (test in tests/test_row_counts.py). Orphan transactions should be counted and reported; consider filtering to “parcel_id IN (SELECT parcel_id FROM parcel_gold)” if a single consistent universe is required.

**Recommendation:** Run test_transaction_gold_parcel_id_foreign_key; if orphans exist, report count and decide whether to restrict transaction_gold to parcels present in parcel_gold.

---

## 3. Distributions and outliers

- **PPSF and living_sq_ft:** transaction_gold filters to sold_price > 0 and living_sq_ft > 0. Extreme PPSF (e.g. very low or very high) can skew city_year and modeling. Analytics already uses a ppsf >= 400 filter for the LA fact MV; gold remains unfiltered for flexibility.
- **LA scope:** parcel_gold includes all parcels with an address (any city). transaction_gold includes all mls_history sales meeting the filters. For LA-only analyses, filter by parcel_gold.city_name = 'LOS ANGELES' (or equivalent) in downstream views or queries. v_fact_sale_clean already applies LA city filter.

**Recommendation:** When building feature tables or aggregates, apply consistent geography and PPSF/size bounds and document in model cards or runbooks.

---

## Summary

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing geometry / year_built | Spatial and feasibility gaps | Profile null %; document; impute or exclude in modeling. |
| Orphan transactions (property_id not in parcel_gold) | city_year and joins can drop rows | Check referential test; optionally restrict transaction_gold to parcel_gold.parcel_id. |
| PPSF/volume outliers and geography | Skewed aggregates and models | Apply explicit filters and document in specs and model cards. |
