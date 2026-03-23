# Tableau setup: F4 Overpay risk

## Data source

- PostgreSQL (read-only). Use `sql/readonly/f4_overpay_risk_executable.sql` for copy-paste; it returns **median_ppsf** and **comp_count** for one ZIP/year. Edit `'90012'`, `2024`, `400` (zip, year, ppsf_min). Then in Tableau (or a calculated field) compute: comp_based_value = median_ppsf × living_sq_ft; pct_above = (list_price - comp_based_value) / comp_based_value × 100; risk_level from pct_above (≤5% low, ≤12% medium, else high).

## Parameters

| Parameter    | Type  | Description        |
|-------------|-------|--------------------|
| zip_code    | String| ZIP for comps      |
| sale_year   | Int   | 2024               |
| list_price  | Float | List/offer price   |
| living_sq_ft| Float | Subject sqft       |
| ppsf_min    | Float | 400                |

## Output (one row from SQL)

| Field        | Description           |
|-------------|------------------------|
| median_ppsf | 50th percentile PPSF  |
| comp_count  | Comps in ZIP × year    |
| geography_used | 'zip'              |

Derived in app/Tableau: comp_based_value, pct_above_comps, risk_level (low/medium/high).

## Use in Tableau

- Run the SQL to get median_ppsf and comp_count.
- Add parameters for list_price and living_sq_ft.
- Calculated field: Comp-based value = [median_ppsf] * [living_sq_ft].
- Calculated field: % above comps = ([list_price] - [Comp-based value]) / [Comp-based value] * 100.
- Calculated field: Risk = IF [% above comps] <= 5 THEN 'low' ELSEIF [% above comps] <= 12 THEN 'medium' ELSE 'high' END.
- Show as cards or in a single-row summary.
