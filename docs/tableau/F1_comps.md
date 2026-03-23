# Tableau setup: F1 Comps selection + display

## Data source

- **Connection:** PostgreSQL (read-only). Use the same DB URL as the FastAPI app.
- **No analytics schema required:** Use the read-only query below so you don't need `CREATE` rights.

## Query to use (read-only mode)

Run this **single SELECT** in Tableau (e.g. New Data Source → PostgreSQL → Custom SQL). Replace parameters with Tableau parameters or literals.

**Parameters to define in Tableau:**

| Parameter name   | Data type | Default | Description                |
|------------------|-----------|---------|----------------------------|
| `sale_year`      | Integer   | 2024    | Sale year for comps        |
| `zip_code`       | String    | (set)   | ZIP code for comps         |
| `limit`          | Integer   | 10      | Max number of comp rows    |
| `ppsf_min`       | Float     | 400     | Minimum PPSF filter       |

**Custom SQL** — use **`sql/readonly/f1_comps_executable.sql`** for a copy-paste run (edit the literals `'90012'`, `2024`, `10`, `400` for zip, year, limit, ppsf_min). Or use the parameterized version below and bind parameters if your driver supports them.

```sql
WITH
addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id, a.street_id, a.zip_code
  FROM property_address a
  ORDER BY a.property_id, a.street_id
),
street_city AS (
  SELECT s.id AS street_id, c.name AS city_name
  FROM street s
  JOIN city c ON c.id = s.city_id
),
geom_one AS (
  SELECT DISTINCT ON (pg.property_id)
    pg.property_id, pg.center_point AS point_4326
  FROM property_geometry pg
  WHERE pg.center_point IS NOT NULL
  ORDER BY pg.property_id
),
base AS (
  SELECT
    h.id AS sale_id,
    h.property_id,
    h.sold_date,
    EXTRACT(YEAR FROM h.sold_date)::int AS sale_year,
    h.sold_price,
    h.living_sq_ft,
    (h.sold_price / NULLIF(h.living_sq_ft, 0))::numeric AS ppsf,
    a.zip_code,
    sc.city_name,
    h.year_built
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  LEFT JOIN geom_one g ON g.property_id = h.property_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date IS NOT NULL
    AND h.sold_date >= DATE '2020-01-01'
    AND (h.sold_price / NULLIF(h.living_sq_ft, 0)) >= :ppsf_min
    AND UPPER(TRIM(sc.city_name)) = 'LOS ANGELES'
    AND a.zip_code = :zip_code
    AND EXTRACT(YEAR FROM h.sold_date) = :sale_year
),
cohort AS (
  SELECT
    COUNT(*)::int AS comp_count,
    CASE
      WHEN COUNT(*) < 20 THEN 'low'
      WHEN COUNT(*) < 50 THEN 'med'
      ELSE 'high'
    END AS confidence_band
  FROM base
)
SELECT
  b.sale_id, b.property_id, b.sold_date, b.sold_price, b.living_sq_ft,
  b.ppsf, b.zip_code, b.city_name, b.year_built,
  c.comp_count, c.confidence_band
FROM base b
CROSS JOIN cohort c
ORDER BY b.sold_date DESC
LIMIT :limit;
```

**If your Tableau/Postgres driver does not support named parameters:** replace `:zip_code`, `:sale_year`, `:limit`, `:ppsf_min` with placeholders (e.g. `$1`, `$2`, `$3`, `$4`) and pass parameters in order, or use a Tableau parameter in the SQL string (e.g. `" + [Zip Code] + "` for zip — ensure injection-safe usage).

## Fields to map in Tableau

| Field             | Role in Tableau      | Notes                          |
|-------------------|----------------------|--------------------------------|
| `sale_id`         | Dimension (unique)   | Row identifier                 |
| `property_id`     | Dimension            |                                |
| `sold_date`       | Dimension / Date     | For sort and filters           |
| `sold_price`      | Measure              | Currency                       |
| `living_sq_ft`    | Measure              |                                |
| `ppsf`            | Measure              | Price per sq ft                 |
| `zip_code`        | Dimension            | Same for all rows in cohort    |
| `city_name`       | Dimension            |                                |
| `year_built`      | Dimension            | May be null                     |
| `comp_count`      | Measure (constant)   | Cohort size; use for alerts     |
| `confidence_band` | Dimension            | low / med / high; use for color |

## Suggested filters and parameters

- **Parameters:** `sale_year` (default 2024), `zip_code` (user input), `limit` (e.g. 10), `ppsf_min` (400).
- **Filters:** Optional filter on `confidence_band` (e.g. exclude `low` if desired).
- **Alert:** If `comp_count` < 30 (or your `min_comps`), show a “Low sample size” warning.

## No lat/lon in read-only mode

This query returns comps **by ZIP only**. For comps by point (lat/lon) you need the production-mode view that uses `analytics.grid_cells_025` (see Production-mode upgrade).
