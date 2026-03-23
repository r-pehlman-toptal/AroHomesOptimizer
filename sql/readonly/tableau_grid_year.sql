-- Grid × year for Tableau map (price heatmap + confidence overlay).
-- Requires analytics schema: run sql/040_grid_cells_025.sql, 041_populate_grid_cells_025.sql, 050_mv_agg_grid_year_ppsf_025.sql (or scripts/refresh_mvs.py) first.
-- Parameters: optional :sale_year (filter to one year).

SELECT
  g.cell_id,
  g.x_idx,
  g.y_idx,
  g.centroid_lon,
  g.centroid_lat,
  g.geom_3310,
  a.sale_year,
  a.comp_count,
  a.median_ppsf,
  a.avg_ppsf,
  a.new_comp_count,
  a.confidence_band
FROM analytics.grid_cells_025 g
JOIN analytics.mv_agg_grid_year_ppsf_025 a ON g.cell_id = a.cell_id
WHERE (:sale_year IS NULL OR a.sale_year = :sale_year)
ORDER BY g.cell_id, a.sale_year;
