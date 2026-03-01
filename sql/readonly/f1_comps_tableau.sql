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
    pg.property_id,
    pg.center_point::geometry AS point_4326
  FROM property_geometry pg
  WHERE pg.center_point IS NOT NULL
  ORDER BY pg.property_id
),
base AS (
  SELECT
    h.id AS sale_id,
    h.property_id,
    h.sold_date,
    h.sold_price,
    h.living_sq_ft,
    (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) AS ppsf,
    a.zip_code,
    sc.city_name,
    h.year_built,
    ST_Y(g.point_4326)::numeric AS lat,
    ST_X(g.point_4326)::numeric AS lon
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  JOIN geom_one g ON g.property_id = h.property_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date >= DATE '2024-01-01'
    AND h.sold_date <  DATE '2025-01-01'
    AND (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) >= 400
    AND UPPER(TRIM(sc.city_name)) = 'LOS ANGELES'
    AND a.zip_code = '90012'
),
cohort AS (
  SELECT
    COUNT(DISTINCT sale_id)::int AS comp_count,
    CASE
      WHEN COUNT(DISTINCT sale_id) < 20 THEN 'low'
      WHEN COUNT(DISTINCT sale_id) < 50 THEN 'med'
      ELSE 'high'
    END AS confidence_band
  FROM base
)
SELECT
  b.*,
  c.comp_count,
  c.confidence_band
FROM base b
CROSS JOIN cohort c
ORDER BY b.sold_date DESC
LIMIT 50