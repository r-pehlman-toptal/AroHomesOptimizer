-- City × year aggregate (Tableau/BI). Read-only from public tables; no analytics schema required.
-- Default: LA from 2020. Edit min_sold_date below if needed.

WITH addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id, a.street_id, a.zip_code
  FROM property_address a
  ORDER BY a.property_id, a.street_id
),
street_city AS (
  SELECT s.id AS street_id, s.city_id, c.name AS city_name
  FROM street s
  JOIN city c ON c.id = s.city_id
),
base AS (
  SELECT
    sc.city_id,
    sc.city_name,
    EXTRACT(YEAR FROM h.sold_date)::int AS sale_year,
    h.sold_price,
    h.id AS sale_id,
    (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) AS ppsf
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date IS NOT NULL
    AND h.sold_date >= DATE '2020-01-01'
    AND (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) >= 400
    AND UPPER(TRIM(sc.city_name)) = 'LOS ANGELES'
)
SELECT
  city_id,
  city_name,
  sale_year,
  COUNT(DISTINCT sale_id)::int AS total_sales,
  SUM(sold_price)::numeric AS total_revenue,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
  AVG(ppsf)::numeric AS avg_ppsf
FROM base
GROUP BY city_id, city_name, sale_year
ORDER BY city_name, sale_year;
