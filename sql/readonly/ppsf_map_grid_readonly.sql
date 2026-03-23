-- PPSF map grid: read-only, public tables only (no analytics schema).
-- Builds a ~0.25-mi grid by rounding lat/lon (0.004 deg ≈ 0.25 mi in LA).
-- Parameters: :sale_year, :limit, :city_name (e.g. LOS ANGELES).

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
geom_valid AS (
  SELECT
    pg.property_id,
    ST_Y(ST_Transform(pg.center_point::geometry, 4326))::numeric AS lat,
    ST_X(ST_Transform(pg.center_point::geometry, 4326))::numeric AS lon
  FROM property_geometry pg
  WHERE pg.center_point IS NOT NULL
    AND ST_IsValid(pg.center_point::geometry)
),
base AS (
  SELECT
    EXTRACT(YEAR FROM h.sold_date)::int AS sale_year,
    (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) AS ppsf,
    g.lat,
    g.lon,
    floor(g.lat / 0.004) AS y_idx,
    floor(g.lon / 0.004) AS x_idx
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  JOIN geom_valid g ON g.property_id = h.property_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date IS NOT NULL
    AND (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) >= 400
    AND UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name))
    AND EXTRACT(YEAR FROM h.sold_date) = :sale_year
)
SELECT
  (x_idx::text || '_' || y_idx::text) AS geo_id,
  (x_idx * 0.004 + 0.002)::float AS centroid_lon,
  (y_idx * 0.004 + 0.002)::float AS centroid_lat,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf)::float AS median_ppsf,
  AVG(ppsf)::float AS avg_ppsf,
  COUNT(*)::int AS comp_count,
  CASE
    WHEN COUNT(*) < 20 THEN 'low'
    WHEN COUNT(*) < 50 THEN 'med'
    ELSE 'high'
  END AS confidence_band
FROM base
GROUP BY x_idx, y_idx
ORDER BY comp_count DESC
LIMIT :limit;
