-- PPSF map: 0.25-mi grid × year. Inline aggregate (no materialized view).
-- Requires analytics: grid_cells_025, mv_sale_la_since2020_ppsf400.
-- Parameters: :sale_year, :limit.

SELECT
  g.cell_id::text AS geo_id,
  g.centroid_lon,
  g.centroid_lat,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.ppsf) AS median_ppsf,
  AVG(s.ppsf) AS avg_ppsf,
  COUNT(*)::int AS comp_count,
  CASE
    WHEN COUNT(*) < 20 THEN 'low'
    WHEN COUNT(*) < 50 THEN 'med'
    ELSE 'high'
  END AS confidence_band
FROM analytics.grid_cells_025 g
JOIN analytics.mv_sale_la_since2020_ppsf400 s
  ON s.point_3310 IS NOT NULL AND ST_Intersects(s.point_3310, g.geom_3310)
WHERE s.sale_year = :sale_year
GROUP BY g.cell_id, g.centroid_lon, g.centroid_lat
ORDER BY comp_count DESC
LIMIT :limit;
