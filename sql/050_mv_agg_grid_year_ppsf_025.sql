-- 050_mv_agg_grid_year_ppsf_025.sql
-- Grid (0.25-mile) x year PPSF metrics. Spatial join uses point_3310 (indexed) for performance.
-- Unique (cell_id, sale_year) for REFRESH CONCURRENTLY.

DROP MATERIALIZED VIEW IF EXISTS analytics.mv_agg_grid_year_ppsf_025 CASCADE;

CREATE MATERIALIZED VIEW analytics.mv_agg_grid_year_ppsf_025 AS
SELECT
  g.cell_id,
  s.sale_year,
  COUNT(DISTINCT s.sale_id) AS comp_count,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.ppsf) AS median_ppsf,
  AVG(s.ppsf) AS avg_ppsf,
  COUNT(DISTINCT CASE WHEN s.year_built >= 2019 THEN s.sale_id END) AS new_comp_count,
  CASE
    WHEN COUNT(DISTINCT s.sale_id) < 20 THEN 'low'
    WHEN COUNT(DISTINCT s.sale_id) < 50 THEN 'med'
    ELSE 'high'
  END AS confidence_band
FROM analytics.grid_cells_025 g
JOIN analytics.mv_sale_la_since2020_ppsf400 s
  ON s.point_3310 IS NOT NULL AND ST_Intersects(s.point_3310, g.geom_3310)
GROUP BY g.cell_id, s.sale_year;

CREATE UNIQUE INDEX ux_mv_agg_grid_year_ppsf_025_cell_year
  ON analytics.mv_agg_grid_year_ppsf_025 (cell_id, sale_year);

CREATE INDEX ix_mv_agg_grid_year_ppsf_025_sale_year
  ON analytics.mv_agg_grid_year_ppsf_025 (sale_year);

COMMENT ON MATERIALIZED VIEW analytics.mv_agg_grid_year_ppsf_025 IS '0.25-mile grid x year: comp_count, median/avg PPSF, new_comp_count, confidence_band.';
