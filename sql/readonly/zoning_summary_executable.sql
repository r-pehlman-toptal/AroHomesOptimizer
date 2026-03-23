-- Zoning summary for one parcel (edit parcel_id below and run).
-- Parameter: parcel_id (integer)

WITH
addr_one AS (
  SELECT DISTINCT ON (a.property_id) a.property_id, a.street_id
  FROM property_address a
  ORDER BY a.property_id, a.street_id
),
geom_one AS (
  SELECT DISTINCT ON (pg.property_id) pg.property_id, pg.lot_size_sq_ft
  FROM property_geometry pg
  ORDER BY pg.property_id
),
zoning_one AS (
  SELECT DISTINCT ON (pz.property_id) pz.property_id, z.name AS zone_code
  FROM property_zoning pz
  JOIN zone z ON z.id = pz.zone_id
  ORDER BY pz.property_id
)
SELECT
  p.property_id AS parcel_id,
  z.zone_code,
  g.lot_size_sq_ft
FROM addr_one p
LEFT JOIN zoning_one z ON z.property_id = p.property_id
LEFT JOIN geom_one g ON g.property_id = p.property_id
WHERE p.property_id = 12345;  -- edit parcel_id
