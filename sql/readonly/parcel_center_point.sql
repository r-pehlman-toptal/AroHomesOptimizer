-- Parcel center point (WGS84) for proximity/distance use (read-only).
-- Parameter: :parcel_id (integer)
-- Returns one row with parcel_id, longitude, latitude (or empty if no geometry).

SELECT
  pg.property_id AS parcel_id,
  ST_X(pg.center_point::geometry) AS longitude,
  ST_Y(pg.center_point::geometry) AS latitude
FROM property_geometry pg
WHERE pg.property_id = :parcel_id
  AND pg.center_point IS NOT NULL
  AND ST_IsValid(pg.center_point::geometry);
