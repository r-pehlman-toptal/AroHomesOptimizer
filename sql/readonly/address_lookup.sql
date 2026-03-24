-- Address lookup: resolve address text to candidate property_ids.
-- Parameters:
--   :property_id (integer, optional) – direct lookup by id.
--   :house_number, :street_normalized (optional) – match "11401 CLOVER AVE" (house_number + street name/suffix).
--   :zip_code, :city_name (optional) – when no property_id/house+street, filter by zip and/or city (up to 5 rows).
-- full_address: when house_number+street matched, "11401 Clover Ave"; else "Property {id}, {zip}, {city}".
-- match_score: 1.0 for property_id or house+street match, 0.7 zip+city, 0.5 zip or city only.

WITH addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id,
    a.street_id,
    a.house_number,
    TRIM(CAST(a.zip_code AS TEXT)) AS zip_code
  FROM property_address a
  WHERE (:property_id IS NOT NULL AND a.property_id = :property_id)
     OR (
         :property_id IS NULL
         AND :house_number IS NULL
         AND :street_normalized IS NULL
         AND (:zip_code IS NULL OR TRIM(CAST(a.zip_code AS TEXT)) = TRIM(CAST(:zip_code AS TEXT)))
         AND (
           :city_name IS NULL
           OR EXISTS (
             SELECT 1 FROM street s
             JOIN city c ON c.id = s.city_id
             WHERE s.id = a.street_id
               AND UPPER(TRIM(c.name)) = UPPER(TRIM(:city_name))
             )
         )
       )
     OR (
         :property_id IS NULL
         AND :house_number IS NOT NULL
         AND :street_normalized IS NOT NULL
         AND TRIM(COALESCE(a.house_number, '')) = TRIM(CAST(:house_number AS TEXT))
         AND EXISTS (
           SELECT 1 FROM street s2
           WHERE s2.id = a.street_id
             AND UPPER(TRIM(BOTH FROM COALESCE(s2.name, '') || ' ' || COALESCE(s2.suffix, ''))) = UPPER(TRIM(:street_normalized))
         )
         AND (:zip_code IS NULL OR TRIM(CAST(a.zip_code AS TEXT)) = TRIM(CAST(:zip_code AS TEXT)))
         AND (
           :city_name IS NULL
           OR EXISTS (
             SELECT 1 FROM street s3
             JOIN city c ON c.id = s3.city_id
             WHERE s3.id = a.street_id
               AND UPPER(TRIM(c.name)) = UPPER(TRIM(:city_name))
             )
         )
       )
  ORDER BY a.property_id, a.street_id
),
with_city AS (
  SELECT
    a.property_id,
    a.zip_code,
    a.house_number,
    c.name AS city_name,
    s.name AS street_name,
    s.suffix AS street_suffix
  FROM addr_one a
  JOIN street s ON s.id = a.street_id
  JOIN city c ON c.id = s.city_id
)
SELECT
  property_id,
  CASE
    WHEN :house_number IS NOT NULL AND :street_normalized IS NOT NULL AND house_number IS NOT NULL
      THEN TRIM(house_number) || ' ' || TRIM(COALESCE(street_name, '')) || COALESCE(' ' || NULLIF(TRIM(COALESCE(street_suffix, '')), ''), '')
    ELSE 'Property ' || property_id || COALESCE(', ' || NULLIF(zip_code, ''), '') || COALESCE(', ' || NULLIF(city_name, ''), '')
  END AS full_address,
  zip_code,
  city_name,
  CASE
    WHEN :property_id IS NOT NULL THEN 1.0
    WHEN :house_number IS NOT NULL AND :street_normalized IS NOT NULL THEN 1.0
    WHEN :zip_code IS NOT NULL AND :city_name IS NOT NULL THEN 0.7
    ELSE 0.5
  END::float AS match_score
FROM with_city
ORDER BY match_score DESC, property_id
LIMIT 5;
