# F3 Offer range (p25/p50/p75) — Summary

## Delivered

| Item | Location |
|------|----------|
| **Read-only SQL** | `sql/readonly/f3_offer_range.sql`, `f3_offer_range_executable.sql` |
| **FastAPI endpoint** | `POST /queries/f3/offer-range` |
| **Request** | `F3OfferRangeParams`: zip_code, living_sq_ft, sale_year=2024, ppsf_min=400 |
| **Response** | One row: low_ppsf, base_ppsf, high_ppsf, low_price, base_price, high_price, comp_count, geography_used |
| **Tableau** | `docs/tableau/F3_offer_range.md` |
| **Web UI plan** | `docs/web_ui/F3_offer_range.md` |
| **Production view** | `sql/production/f3_offer_range_production.sql` (ZIP × year percentiles; multiply by living_sq_ft in query or app) |

## Read-only behavior

- ZIP only. One row per request: 25th/50th/75th percentile PPSF for that ZIP × year, then × living_sq_ft for price range. Empty list if no comps.
