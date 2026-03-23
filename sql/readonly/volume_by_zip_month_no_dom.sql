-- Volume by ZIP × month without days_on_market (use when mls_history has no days_on_market).
-- Parameters: optional :zip_code, :min_sold_date.

WITH addr_one AS (
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
base AS (
  SELECT
    a.zip_code,
    DATE_TRUNC('month', h.sold_date)::date AS sale_month,
    h.sold_price,
    (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) AS ppsf
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date IS NOT NULL
    AND h.sold_date >= :min_sold_date
    AND UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name))
    AND (:zip_code IS NULL OR a.zip_code = :zip_code)
)
SELECT
  zip_code,
  sale_month,
  COUNT(*)::int AS sale_count,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
  NULL::float AS median_dom
FROM base
GROUP BY zip_code, sale_month
ORDER BY zip_code, sale_month;
