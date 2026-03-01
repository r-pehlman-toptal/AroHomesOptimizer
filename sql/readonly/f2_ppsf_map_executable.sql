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
  SELECT
    h.id AS sale_id,
    a.zip_code,
    EXTRACT(YEAR FROM h.sold_date)::int AS sale_year,
    (h.sold_price / NULLIF(h.living_sq_ft, 0))::numeric AS ppsf
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date IS NOT NULL
    AND h.sold_date >= DATE '2020-01-01'
    AND (h.sold_price / NULLIF(h.living_sq_ft, 0)) >= 400
    AND UPPER(TRIM(sc.city_name)) = 'LOS ANGELES'
    AND a.zip_code IS NOT NULL
)
SELECT
  zip_code AS geo_id,
  NULL::double precision AS centroid_lon,
  NULL::double precision AS centroid_lat,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
  AVG(ppsf) AS avg_ppsf,
  COUNT(*)::int AS comp_count,
  CASE
    WHEN COUNT(*) < 20 THEN 'low'
    WHEN COUNT(*) < 50 THEN 'med'
    ELSE 'high'
  END AS confidence_band
FROM base
WHERE sale_year = 2024
GROUP BY zip_code
ORDER BY comp_count DESC
LIMIT 500;
