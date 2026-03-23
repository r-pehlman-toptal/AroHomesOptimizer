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

**Confidence summary:** Use F1 comps; each row has `comp_count` and `confidence_band`. Derive a summary (e.g. message) in the UI from the first row.

To run with different values, edit the literals in the `*_executable.sql` files.
