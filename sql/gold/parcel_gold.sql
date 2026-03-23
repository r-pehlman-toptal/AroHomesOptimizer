-- parcel_gold: one row per parcel (property_id) for optimization and aggregates.
-- Source: property_address (driver), street, city, property_geometry, mls_history (year_built).
-- Spec: notes/parcel_gold_spec.md. Data map: docs/data-map.md.

CREATE OR REPLACE VIEW parcel_gold AS
WITH
-- One address per property (deterministic: smallest street_id).
addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id,
    a.street_id,
    a.zip_code
  FROM property_address a
  ORDER BY a.property_id, a.street_id
),
-- One geometry per property.
geom_one AS (
  SELECT DISTINCT ON (pg.property_id)
    pg.property_id,
    pg.center_point AS center_point_4326,
    pg.lot_size_sq_ft
  FROM property_geometry pg
  ORDER BY pg.property_id
),
-- Latest sale year_built per property (for parcels with at least one sale).
year_built_one AS (
  SELECT DISTINCT ON (m.property_id)
    m.property_id,
    m.year_built
  FROM mls_history m
  WHERE m.year_built IS NOT NULL
  ORDER BY m.property_id, m.sold_date DESC NULLS LAST
)
SELECT
  pa.property_id AS parcel_id,
  pa.street_id,
  pa.zip_code,
  s.city_id,
  c.name AS city_name,
  c.name AS city,  -- alias for city_year and other consumers that expect "city"
  c.county,
  g.center_point_4326,
  g.lot_size_sq_ft,
  y.year_built
FROM addr_one pa
JOIN street s ON s.id = pa.street_id
JOIN city c ON c.id = s.city_id
LEFT JOIN geom_one g ON g.property_id = pa.property_id
LEFT JOIN year_built_one y ON y.property_id = pa.property_id;

COMMENT ON VIEW parcel_gold IS 'One row per parcel (property_id). Address, city, optional geometry and year_built. Spec: notes/parcel_gold_spec.md';
