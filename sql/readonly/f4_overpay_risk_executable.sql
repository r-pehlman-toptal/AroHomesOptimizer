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
base AS (
  SELECT (h.sold_price / NULLIF(h.living_sq_ft, 0))::numeric AS ppsf
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date IS NOT NULL
    AND h.sold_date >= DATE '2020-01-01'
    AND (h.sold_price / NULLIF(h.living_sq_ft, 0)) >= 400
    AND UPPER(TRIM(sc.city_name)) = 'LOS ANGELES'
    AND a.zip_code = '90012'
    AND EXTRACT(YEAR FROM h.sold_date) = 2024
)
SELECT
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
  COUNT(*)::int AS comp_count,
  'zip' AS geography_used
FROM base;
