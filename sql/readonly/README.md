# Read-only SQL (no CREATE / COMMENT)

Use these when you have **read-only** DB access. All are **SELECT only**; no views, MVs, or COMMENT.

| File | Use |
|------|-----|
| **f1_comps.sql** | Parameterized: `:zip_code`, `:sale_year`, `:limit`, `:ppsf_min`. Used by FastAPI. |
| **f1_comps_executable.sql** | Full executable: edit literals (zip `'90012'`, year `2024`, `LIMIT 10`, ppsf `400`) and run in any client. |
| **f3_offer_range.sql** | Parameterized: `:zip_code`, `:sale_year`, `:living_sq_ft`, `:ppsf_min`. |
| **f3_offer_range_executable.sql** | Full executable: edit `'90012'`, `2024`, `1500`, `400` (zip, year, living_sq_ft, ppsf_min). |
| **f4_overpay_risk.sql** | Parameterized: `:zip_code`, `:sale_year`, `:ppsf_min`. Returns median_ppsf, comp_count. |
| **f4_overpay_risk_executable.sql** | Full executable: edit `'90012'`, `2024`, `400`. Compute comp_based_value and risk in app. |
| **comps_aggregate.sql** | How much – aggregate: subject_parcel_id, subject_sqft, 12-month recency, distance cap, size band, property_subtype. Returns comp_count, median_ppsf, p25/p75, iqr, median_dom, similarity diagnostics. Confidence score/band computed in app. |
| **comps_aggregate_rows.sql** | Row-level comps with weights (same params + `:limit`). Returns sale_id, dist_miles, months_ago, w. |
| **volume_by_zip_year.sql** | Per ZIP × year: sale_count, median_ppsf, median_dom. Params: `:min_sold_date`, optional `:zip_code`. |
| **volume_by_zip_year_executable.sql** | Same as above; literals (from 2020). Tableau paste-and-run. |
| **volume_by_zip_month.sql** | Per ZIP × month: sale_count, median_ppsf, median_dom. Params: `:min_sold_date`, optional `:zip_code`. |
| **volume_by_zip_month_executable.sql** | Same; literals from 2020. Tableau paste-and-run. |
| **volume_by_city_year.sql** | City × year: total_sales, total_revenue, median_ppsf, avg_ppsf. Read-only from public tables. Params: `:min_sold_date`, optional `:city_name`. |
| **volume_by_city_year_executable.sql** | Same; LA from 2020. Tableau paste-and-run. |
| **tableau_grid_year.sql** | Grid × year for map: join analytics.grid_cells_025 + mv_agg_grid_year_ppsf_025. Requires analytics schema. Optional `:sale_year`. |
| **homes_added_to_market_la.sql** | Approx. “homes added to market” in LA: count sales where inferred list date (sold_date − days_on_market) is in period. Params: `:period_start`, `:period_end`, optional `:city_name`. |
| **zoning_summary.sql** | Week 3: `:parcel_id`. Zone + lot_size_sq_ft; constraints applied in app from zone lookup. |
| **zoning_summary_executable.sql** | Edit parcel_id and run. |
| **parcel_center_point.sql** | Week 3: `:parcel_id`. Longitude, latitude (WGS84) for proximity. |
| **nearby_zoning.sql** | Week 3: `:parcel_id`, `:limit`. Subject + nearby parcels (same ZIP) with zone_code. |

**Confidence summary:** Use F1 comps; each row has `comp_count` and `confidence_band`. For comps_aggregate, confidence is from coverage + proximity + recency + tightness (see `src/query_service/comps_confidence.py`).

To run with different values, edit the literals in the `*_executable.sql` files.
