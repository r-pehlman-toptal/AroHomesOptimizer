-- 055_grid_year_tiers_fallback.sql
-- Tiered comp fallback for inference sample size:
--   Tier 1: 0.25-mile cell
--   Tier 2: 3×3 cells (~0.75-mile)
--   Tier 3: 5×5 cells (~1.25-mile)
--   Tier 4: ZIP
--   Tier 5: City
-- Run after 050. Depends on mv_agg_grid_year_ppsf_025, grid_cells_025, mv_agg_city_year_metrics, and fact MV with zip_code.

-- Zip × year comp counts (for fallback tier 4).
DROP VIEW IF EXISTS analytics.v_zip_year_comp CASCADE;
CREATE VIEW analytics.v_zip_year_comp AS
SELECT
  zip_code,
  sale_year,
  COUNT(DISTINCT sale_id) AS comp_zip
FROM analytics.mv_sale_la_since2020_ppsf400
WHERE zip_code IS NOT NULL
GROUP BY zip_code, sale_year;

-- Per (cell_id, sale_year): primary_zip and primary_city_id (mode of sales in that cell).
DROP VIEW IF EXISTS analytics.v_cell_year_primary_geo CASCADE;
CREATE VIEW analytics.v_cell_year_primary_geo AS
WITH cell_zip_rank AS (
  SELECT
    g.cell_id,
    s.sale_year,
    s.zip_code,
    ROW_NUMBER() OVER (PARTITION BY g.cell_id, s.sale_year ORDER BY COUNT(*) DESC) AS rn_zip
  FROM analytics.grid_cells_025 g
  JOIN analytics.mv_sale_la_since2020_ppsf400 s
    ON s.point_3310 IS NOT NULL AND ST_Intersects(s.point_3310, g.geom_3310)
  WHERE s.zip_code IS NOT NULL
  GROUP BY g.cell_id, s.sale_year, s.zip_code
),
cell_city_rank AS (
  SELECT
    g.cell_id,
    s.sale_year,
    s.city_id,
    ROW_NUMBER() OVER (PARTITION BY g.cell_id, s.sale_year ORDER BY COUNT(*) DESC) AS rn_city
  FROM analytics.grid_cells_025 g
  JOIN analytics.mv_sale_la_since2020_ppsf400 s
    ON s.point_3310 IS NOT NULL AND ST_Intersects(s.point_3310, g.geom_3310)
  GROUP BY g.cell_id, s.sale_year, s.city_id
)
SELECT
  z.cell_id,
  z.sale_year,
  z.zip_code   AS primary_zip,
  c.city_id    AS primary_city_id
FROM (SELECT cell_id, sale_year, zip_code FROM cell_zip_rank WHERE rn_zip = 1) z
JOIN (SELECT cell_id, sale_year, city_id FROM cell_city_rank WHERE rn_city = 1) c
  ON z.cell_id = c.cell_id AND z.sale_year = c.sale_year;

-- Tiers: comp_025, comp_3x3, comp_5x5, comp_zip, comp_city per (cell_id, sale_year).
DROP VIEW IF EXISTS analytics.v_grid_year_comp_tiers CASCADE;
CREATE VIEW analytics.v_grid_year_comp_tiers AS
WITH base AS (
  SELECT
    agg.cell_id,
    g.x_idx,
    g.y_idx,
    agg.sale_year,
    agg.comp_count AS comp_025
  FROM analytics.mv_agg_grid_year_ppsf_025 agg
  JOIN analytics.grid_cells_025 g ON g.cell_id = agg.cell_id
),
neighbors_3x3 AS (
  SELECT
    b.cell_id,
    b.sale_year,
    SUM(n.comp_count) AS comp_3x3
  FROM base b
  JOIN analytics.grid_cells_025 gb ON gb.cell_id = b.cell_id
  JOIN analytics.grid_cells_025 gn
    ON gn.x_idx BETWEEN gb.x_idx - 1 AND gb.x_idx + 1
   AND gn.y_idx BETWEEN gb.y_idx - 1 AND gb.y_idx + 1
  JOIN analytics.mv_agg_grid_year_ppsf_025 n
    ON n.cell_id = gn.cell_id AND n.sale_year = b.sale_year
  GROUP BY b.cell_id, b.sale_year
),
neighbors_5x5 AS (
  SELECT
    b.cell_id,
    b.sale_year,
    SUM(n.comp_count) AS comp_5x5
  FROM base b
  JOIN analytics.grid_cells_025 gb ON gb.cell_id = b.cell_id
  JOIN analytics.grid_cells_025 gn
    ON gn.x_idx BETWEEN gb.x_idx - 2 AND gb.x_idx + 2
   AND gn.y_idx BETWEEN gb.y_idx - 2 AND gb.y_idx + 2
  JOIN analytics.mv_agg_grid_year_ppsf_025 n
    ON n.cell_id = gn.cell_id AND n.sale_year = b.sale_year
  GROUP BY b.cell_id, b.sale_year
)
SELECT
  b.cell_id,
  b.sale_year,
  b.comp_025,
  n3.comp_3x3,
  n5.comp_5x5,
  COALESCE(zy.comp_zip, 0) AS comp_zip,
  COALESCE(cy.total_sales, 0) AS comp_city,
  p.primary_zip,
  p.primary_city_id
FROM base b
LEFT JOIN neighbors_3x3 n3 ON n3.cell_id = b.cell_id AND n3.sale_year = b.sale_year
LEFT JOIN neighbors_5x5 n5 ON n5.cell_id = b.cell_id AND n5.sale_year = b.sale_year
LEFT JOIN analytics.v_cell_year_primary_geo p ON p.cell_id = b.cell_id AND p.sale_year = b.sale_year
LEFT JOIN analytics.v_zip_year_comp zy ON zy.zip_code = p.primary_zip AND zy.sale_year = b.sale_year
LEFT JOIN analytics.mv_agg_city_year_metrics cy ON cy.city_id = p.primary_city_id AND cy.sale_year = b.sale_year;

-- Effective tier: first tier with comp >= min_threshold (default 20). Use in dashboards to decide geography for inference.
DROP VIEW IF EXISTS analytics.v_grid_year_effective_tier CASCADE;
CREATE VIEW analytics.v_grid_year_effective_tier AS
SELECT
  cell_id,
  sale_year,
  comp_025,
  comp_3x3,
  comp_5x5,
  comp_zip,
  comp_city,
  primary_zip,
  primary_city_id,
  CASE
    WHEN comp_025 >= 20 THEN 1
    WHEN comp_3x3 >= 20 THEN 2
    WHEN comp_5x5 >= 20 THEN 3
    WHEN comp_zip >= 20 THEN 4
    WHEN comp_city >= 20 THEN 5
    ELSE 5
  END AS effective_tier,
  CASE
    WHEN comp_025 >= 20 THEN comp_025
    WHEN comp_3x3 >= 20 THEN comp_3x3
    WHEN comp_5x5 >= 20 THEN comp_5x5
    WHEN comp_zip >= 20 THEN comp_zip
    ELSE comp_city
  END AS effective_comp_count,
  CASE
    WHEN comp_025 >= 20 THEN 'cell_025'
    WHEN comp_3x3 >= 20 THEN 'cell_3x3'
    WHEN comp_5x5 >= 20 THEN 'cell_5x5'
    WHEN comp_zip >= 20 THEN 'zip'
    ELSE 'city'
  END AS effective_geometry_type
FROM analytics.v_grid_year_comp_tiers;

COMMENT ON VIEW analytics.v_zip_year_comp IS 'Zip × year comp counts for tier-4 fallback.';
COMMENT ON VIEW analytics.v_cell_year_primary_geo IS 'Per (cell_id, sale_year): mode zip and city_id of sales in that cell.';
COMMENT ON VIEW analytics.v_grid_year_comp_tiers IS 'Comp counts at tier 1 (0.25-mi) through 5 (city).';
COMMENT ON VIEW analytics.v_grid_year_effective_tier IS 'Effective tier (1–5) and comp count using min 20 comps; use to choose geography for inference.';
