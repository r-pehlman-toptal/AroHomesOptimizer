-- Lot sizes for parcels in a region (ZIP and/or city). For heatmap of lot size distribution.
-- Parameters: :city_name, optional :zip_code, optional :min_year_built/:max_year_built (if set, only parcels with building built in this range), :limit (default 5000).
-- Read-only; uses property_geometry, property_address, street, city; when year_built range set also uses mls_history.

WITH addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id,
    a.street_id,
    a.zip_code
  FROM property_address a
  ORDER BY a.property_id, a.street_id
),
street_city AS (
  SELECT s.id AS street_id, c.name AS city_name
  FROM street s
  JOIN city c ON c.id = s.city_id
),
region_property AS (
  SELECT a.property_id
  FROM addr_one a
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name))
    AND (:zip_code IS NULL OR a.zip_code = :zip_code)
),
built_in_period AS (
  SELECT DISTINCT h.property_id
  FROM mls_history h
  JOIN region_property rp ON rp.property_id = h.property_id
  WHERE :min_year_built IS NOT NULL
    AND :max_year_built IS NOT NULL
    AND h.year_built >= :min_year_built
    AND h.year_built <= :max_year_built
)
SELECT pg.lot_size_sq_ft
FROM property_geometry pg
JOIN region_property rp ON rp.property_id = pg.property_id
LEFT JOIN built_in_period b ON b.property_id = pg.property_id
WHERE pg.lot_size_sq_ft IS NOT NULL
  AND pg.lot_size_sq_ft > 0
  AND (:min_year_built IS NULL OR :max_year_built IS NULL OR b.property_id IS NOT NULL)
ORDER BY pg.property_id
LIMIT :limit;
