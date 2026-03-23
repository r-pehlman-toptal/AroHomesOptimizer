-- Grid-year aggregates for submarket/map analysis.
-- Requires analytics schema: mv_agg_grid_year_ppsf_025, grid_cells_025 (run sql/030, 040, 041, 050 or scripts/refresh_mvs.py first).
-- Creates a single view joining grid × year metrics with cell centroids for mapping and dashboards.

CREATE OR REPLACE VIEW grid_year AS
SELECT
  a.cell_id,
  a.sale_year,
  a.comp_count,
  a.median_ppsf,
  a.avg_ppsf,
  a.new_comp_count,
  a.confidence_band,
  g.centroid_lat,
  g.centroid_lon
FROM analytics.mv_agg_grid_year_ppsf_025 a
JOIN analytics.grid_cells_025 g ON g.cell_id = a.cell_id;
