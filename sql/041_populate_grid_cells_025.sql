-- 041_populate_grid_cells_025.sql
-- Populate or repopulate grid from current extent of mv_sale_la_since2020_ppsf400.
-- Run after 020 is refreshed. Safe to run multiple times (truncate then insert).

TRUNCATE analytics.grid_cells_025;

INSERT INTO analytics.grid_cells_025 (cell_id, x_idx, y_idx, geom_3310, centroid_lon, centroid_lat)
WITH extent AS (
  SELECT
    402.336 AS cell_size_m,
    ST_Extent(point_3310) AS e
  FROM analytics.mv_sale_la_since2020_ppsf400
  WHERE point_3310 IS NOT NULL
),
bounds AS (
  SELECT
    cell_size_m,
    ST_XMin(e) AS x0,
    ST_YMin(e) AS y0,
    ST_XMax(e) AS x1,
    ST_YMax(e) AS y1
  FROM extent
  WHERE e IS NOT NULL
),
series AS (
  SELECT
    b.cell_size_m,
    b.x0,
    b.y0,
    gx.x AS x_idx,
    gy.y AS y_idx,
    b.x0 + (gx.x * b.cell_size_m) AS x_min,
    b.y0 + (gy.y * b.cell_size_m) AS y_min
  FROM bounds b
  CROSS JOIN generate_series(
    floor(b.x0 / b.cell_size_m)::int,
    ceiling(b.x1 / b.cell_size_m)::int - 1
  ) AS gx(x)
  CROSS JOIN generate_series(
    floor(b.y0 / b.cell_size_m)::int,
    ceiling(b.y1 / b.cell_size_m)::int - 1
  ) AS gy(y)
),
cells AS (
  SELECT
    x_idx,
    y_idx,
    ST_SetSRID(ST_MakeEnvelope(
      x_min,
      y_min,
      x_min + cell_size_m,
      y_min + cell_size_m
    ), 3310) AS geom_3310
  FROM series
)
SELECT
  x_idx::text || '_' || y_idx::text AS cell_id,
  x_idx,
  y_idx,
  geom_3310,
  ST_X(ST_Transform(ST_Centroid(geom_3310), 4326)) AS centroid_lon,
  ST_Y(ST_Transform(ST_Centroid(geom_3310), 4326)) AS centroid_lat
FROM cells;
