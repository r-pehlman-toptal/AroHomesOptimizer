-- 040_grid_cells_025.sql
-- 0.25-mile (402.336 m) grid in EPSG:3310. Deterministic cell_id = x_idx_y_idx.
-- Extent derived from LA sales (mv_sale_la_since2020_ppsf400). Run after 020 is populated.

-- TODO: If la_boundary (polygon) exists, use ST_Extent(ST_Transform(la_boundary.geom, 3310)) for extent.

DROP TABLE IF EXISTS analytics.grid_cells_025 CASCADE;

CREATE TABLE analytics.grid_cells_025 (
  cell_id     text PRIMARY KEY,
  x_idx       int NOT NULL,
  y_idx       int NOT NULL,
  geom_3310   geometry(Polygon, 3310) NOT NULL,
  centroid_lon numeric,
  centroid_lat numeric
);

-- Populate from extent of LA sales. No-op if MV empty (INSERT SELECT returns 0 rows).
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

CREATE INDEX ix_grid_cells_025_geom_3310
  ON analytics.grid_cells_025 USING GIST (geom_3310);

CREATE INDEX ix_grid_cells_025_xy ON analytics.grid_cells_025 (x_idx, y_idx);

COMMENT ON TABLE analytics.grid_cells_025 IS '0.25-mile grid (402.336m) EPSG:3310; extent from LA sales. cell_id = x_idx_y_idx.';
