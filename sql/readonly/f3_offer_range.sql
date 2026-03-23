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
    AND (h.sold_price / NULLIF(h.living_sq_ft, 0)) >= :ppsf_min
    AND UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name))
    AND a.zip_code = :zip_code
    AND EXTRACT(YEAR FROM h.sold_date) = :sale_year
),
pct AS (
  SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ppsf) AS p25,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ppsf) AS p75,
    COUNT(*)::int AS comp_count
  FROM base
)
SELECT
  p25 AS low_ppsf,
  p50 AS base_ppsf,
  p75 AS high_ppsf,
  (p25 * :living_sq_ft) AS low_price,
  (p50 * :living_sq_ft) AS base_price,
  (p75 * :living_sq_ft) AS high_price,
  comp_count,
  'zip' AS geography_used
FROM pct;
