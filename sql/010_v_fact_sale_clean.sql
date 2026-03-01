-- 010_v_fact_sale_clean.sql
-- Base clean view: ONE row per sale (mls_history.id), no join fan-out.
-- Uses LATERAL / single-row subqueries to pick one address, one geometry, one attom row per property.
-- Safe casts and NULLIF for ppsf. Provides point_4326 and point_3310 for grid/spatial work.

-- TODO: If la_boundary (polygon) is available, replace city-name filter with:
--   AND EXISTS (SELECT 1 FROM la_boundary lb WHERE ST_Intersects(geom_4326, lb.geom))
-- Location filter: fallback to city.name = 'Los Angeles' until boundary polygon is provided.

DROP VIEW IF EXISTS analytics.v_fact_sale_clean;

CREATE OR REPLACE VIEW analytics.v_fact_sale_clean AS
WITH
-- One address per property: deterministic single row (min street_id). If is_primary/updated_at exist, prefer them.
addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id,
    a.street_id,
    a.zip_code
  FROM property_address a
  ORDER BY a.property_id,
    -- Uncomment if columns exist: COALESCE((a.is_primary = true), false) DESC, a.updated_at DESC NULLS LAST,
    a.street_id
),
-- One geometry per property (latest or only); transform to 3310 for grid/distance.
geom_one AS (
  SELECT DISTINCT ON (pg.property_id)
    pg.property_id,
    pg.center_point AS point_4326,
    ST_Transform(pg.center_point::geometry, 3310) AS point_3310
  FROM property_geometry pg
  WHERE pg.center_point IS NOT NULL
  ORDER BY pg.property_id
),
-- City per street (one row per street).
street_city AS (
  SELECT s.id AS street_id, s.city_id, c.name AS city_name
  FROM street s
  JOIN city c ON c.id = s.city_id
)
SELECT
  h.id AS sale_id,
  h.property_id,
  h.sold_date,
  EXTRACT(YEAR FROM h.sold_date)::int AS sale_year,
  h.sold_price,
  h.living_sq_ft,
  (h.sold_price / NULLIF(h.living_sq_ft, 0))::numeric AS ppsf,
  sc.city_id,
  sc.city_name,
  a.zip_code,
  g.point_4326,
  g.point_3310,
  h.year_built   -- remove if mls_history has no year_built; then drop from 020/050 or add via assessor join
FROM mls_history h
JOIN addr_one a ON a.property_id = h.property_id
JOIN street_city sc ON sc.street_id = a.street_id
LEFT JOIN geom_one g ON g.property_id = h.property_id
WHERE h.sold_price > 0
  AND h.living_sq_ft > 0
  AND h.sold_date IS NOT NULL
  -- LA location: fallback until la_boundary.geom is available
  AND UPPER(TRIM(sc.city_name)) = 'LOS ANGELES';

COMMENT ON VIEW analytics.v_fact_sale_clean IS 'One row per sale; no fan-out. LA only (city name fallback). point_4326/3310 for mapping and grid.';
