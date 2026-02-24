-- 090_refresh_concurrently.sql
-- Run these after MVs and unique indexes exist. For initial empty build, use:
--   CREATE MATERIALIZED VIEW ... WITH NO DATA;
--   REFRESH MATERIALIZED VIEW CONCURRENTLY ...;

REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_sale_la_since2020_ppsf400;
REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_agg_city_year_metrics;
REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_agg_grid_year_ppsf_025;
