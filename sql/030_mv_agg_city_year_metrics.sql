-- 030_mv_agg_city_year_metrics.sql
-- City x year aggregate: total_revenue, total_sales, avg_ppsf, median_ppsf.
-- Built from mv_sale_la_since2020_ppsf400. Unique (city_id, sale_year) for concurrent refresh.

DROP MATERIALIZED VIEW IF EXISTS analytics.mv_agg_city_year_metrics CASCADE;

CREATE MATERIALIZED VIEW analytics.mv_agg_city_year_metrics AS
SELECT
  city_id,
  sale_year,
  city_name,
  SUM(sold_price) AS total_revenue,
  COUNT(DISTINCT sale_id) AS total_sales,
  AVG(ppsf) AS avg_ppsf,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf
FROM analytics.mv_sale_la_since2020_ppsf400
GROUP BY city_id, sale_year, city_name;

CREATE UNIQUE INDEX ux_mv_agg_city_year_metrics_city_year
  ON analytics.mv_agg_city_year_metrics (city_id, sale_year);

CREATE INDEX ix_mv_agg_city_year_metrics_sale_year
  ON analytics.mv_agg_city_year_metrics (sale_year);

COMMENT ON MATERIALIZED VIEW analytics.mv_agg_city_year_metrics IS 'City x year metrics for Tableau/dashboards; from LA filtered fact.';
