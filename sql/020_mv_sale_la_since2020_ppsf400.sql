-- 020_mv_sale_la_since2020_ppsf400.sql
-- Filtered fact: LA, sold_date >= 2020-01-01, ppsf >= 400. One row per sale.
-- Unique index on sale_id required for REFRESH MATERIALIZED VIEW CONCURRENTLY.
-- Indexes support: time filters (sold_date, sale_year), city/year grouping, spatial join (GiST point_3310).

-- Drop in reverse dependency order if re-running.
DROP MATERIALIZED VIEW IF EXISTS analytics.mv_sale_la_since2020_ppsf400 CASCADE;

CREATE MATERIALIZED VIEW analytics.mv_sale_la_since2020_ppsf400 AS
SELECT
  sale_id,
  property_id,
  sold_date,
  sale_year,
  sold_price,
  living_sq_ft,
  ppsf,
  city_id,
  city_name,
  point_4326,
  point_3310,
  year_built
FROM analytics.v_fact_sale_clean
WHERE sold_date >= DATE '2020-01-01'
  AND ppsf >= 400;

-- Required for REFRESH MATERIALIZED VIEW CONCURRENTLY: unique index.
CREATE UNIQUE INDEX ux_mv_sale_la_since2020_ppsf400_sale_id
  ON analytics.mv_sale_la_since2020_ppsf400 (sale_id);

-- Speeds up time-bounded dashboard queries and city/year aggregates.
CREATE INDEX ix_mv_sale_la_since2020_ppsf400_sale_year
  ON analytics.mv_sale_la_since2020_ppsf400 (sale_year);

CREATE INDEX ix_mv_sale_la_since2020_ppsf400_city_year
  ON analytics.mv_sale_la_since2020_ppsf400 (city_id, sale_year);

CREATE INDEX ix_mv_sale_la_since2020_ppsf400_sold_date
  ON analytics.mv_sale_la_since2020_ppsf400 (sold_date);

-- Spatial: grid join and map extent queries; use 3310 to match grid cells (no transform in join).
CREATE INDEX ix_mv_sale_la_since2020_ppsf400_point_3310
  ON analytics.mv_sale_la_since2020_ppsf400 USING GIST (point_3310);

COMMENT ON MATERIALIZED VIEW analytics.mv_sale_la_since2020_ppsf400 IS 'LA sales from 2020-01-01, ppsf>=400. Source for city/year and grid/year MVs.';
