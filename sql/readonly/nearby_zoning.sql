-- Nearby zoning: subject parcel + other parcels in same ZIP with their zone(s). Read-only.
-- Parameters: :parcel_id (subject), :limit (max nearby parcels to return, default 20)

WITH
addr_one AS (
  SELECT DISTINCT ON (a.property_id) a.property_id, a.zip_code
  FROM property_address a
  ORDER BY a.property_id
),
subject_zip AS (
  SELECT zip_code FROM addr_one WHERE property_id = :parcel_id LIMIT 1
),
zoning_one AS (
  SELECT DISTINCT ON (pz.property_id) pz.property_id, z.name AS zone_code
  FROM property_zoning pz
  JOIN zone z ON z.id = pz.zone_id
  ORDER BY pz.property_id
),
parcels_in_zip AS (
  SELECT a.property_id AS parcel_id, a.zip_code
  FROM addr_one a
  JOIN subject_zip s ON s.zip_code = a.zip_code
),
with_zone AS (
  SELECT p.parcel_id, p.zip_code, z.zone_code
  FROM parcels_in_zip p
  LEFT JOIN zoning_one z ON z.property_id = p.parcel_id
)
SELECT
  parcel_id,
  zip_code,
  zone_code,
  (parcel_id = :parcel_id) AS is_subject
FROM with_zone
ORDER BY is_subject DESC, parcel_id
LIMIT :limit;
