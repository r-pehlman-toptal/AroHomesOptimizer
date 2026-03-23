# Tableau setup: F3 Offer range (p25/p50/p75)

## Data source

- PostgreSQL (read-only). Use `sql/readonly/f3_offer_range_executable.sql` for copy-paste; edit literals `'90012'`, `2024`, `1500`, `400` (zip, year, living_sq_ft, ppsf_min).

## Parameters

| Parameter    | Type  | Default | Description        |
|-------------|-------|--------|--------------------|
| zip_code    | String| —      | ZIP for comps      |
| sale_year   | Int   | 2024   | Sale year          |
| living_sq_ft| Float | —      | Subject sqft       |
| ppsf_min    | Float | 400    | Min PPSF filter    |

## Output (one row)

| Field           | Description                    |
|-----------------|--------------------------------|
| low_ppsf        | 25th percentile PPSF           |
| base_ppsf       | 50th percentile PPSF           |
| high_ppsf       | 75th percentile PPSF           |
| low_price       | low_ppsf × living_sq_ft        |
| base_price      | base_ppsf × living_sq_ft       |
| high_price      | high_ppsf × living_sq_ft        |
| comp_count      | Number of comps in ZIP × year  |
| geography_used  | 'zip'                          |

Use as a single-row summary or in a dashboard card for recommended offer range.
