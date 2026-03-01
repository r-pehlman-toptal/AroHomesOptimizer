# F4 Overpay risk — Summary

## Delivered

| Item | Location |
|------|----------|
| **Read-only SQL** | `sql/readonly/f4_overpay_risk.sql`, `f4_overpay_risk_executable.sql` |
| **FastAPI endpoint** | `POST /queries/f4/overpay-risk` |
| **Request** | `F4OverpayRiskParams`: zip_code, list_price, living_sq_ft, sale_year=2024, ppsf_min=400 |
| **Response** | One row: comp_median_ppsf, comp_based_value, list_price, pct_above_comps, risk_level, comp_count, geography_used |
| **Tableau** | `docs/tableau/F4_overpay_risk.md` |
| **Web UI plan** | `docs/web_ui/F4_overpay_risk.md` |
| **Production view** | `sql/production/f4_overpay_risk_production.sql` (ZIP × year median_ppsf; app computes value and risk) |

## Logic

- Comp-based value = median_ppsf × living_sq_ft. pct_above_comps = (list_price - comp_based_value) / comp_based_value × 100. risk_level: ≤5% low, ≤12% medium, else high.
