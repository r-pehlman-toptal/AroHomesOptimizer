-- Home sizes (living_sq_ft) for parcels in a region. Same idea as region_lot_sizes: one row per parcel.
-- Parameters: :zip_code, :city_name (blank = no city filter), :min_year_built, :max_year_built, :limit.
-- When year range set: only parcels that have at least one mls_history row with year_built in range; living_sq_ft from that sale (latest per parcel).

WITH addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id,
    a.street_id,
    a.zip_code
  FROM property_address a
  WHERE TRIM(CAST(a.zip_code AS TEXT)) = TRIM(CAST(:zip_code AS TEXT))
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
  WHERE (TRIM(COALESCE(CAST(:city_name AS TEXT), '')) = '' OR UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name)))
),
built_in_period AS (
  SELECT rp.property_id
  FROM region_property rp
  LEFT JOIN (
    SELECT DISTINCT h.property_id
    FROM mls_history h
    WHERE :min_year_built IS NOT NULL
      AND :max_year_built IS NOT NULL
      AND h.year_built >= :min_year_built
      AND h.year_built <= :max_year_built
  ) y ON y.property_id = rp.property_id
  WHERE (:min_year_built IS NULL OR :max_year_built IS NULL) OR y.property_id IS NOT NULL
),
parcel_home AS (
  SELECT DISTINCT ON (h.property_id)
    h.property_id,
    h.living_sq_ft
  FROM mls_history h
  JOIN region_property rp ON rp.property_id = h.property_id
  JOIN built_in_period b ON b.property_id = h.property_id
  WHERE h.living_sq_ft IS NOT NULL
    AND h.living_sq_ft > 0
    AND (:min_year_built IS NULL OR :max_year_built IS NULL OR (h.year_built >= :min_year_built AND h.year_built <= :max_year_built))
  ORDER BY h.property_id, h.sold_date DESC
)
SELECT ph.living_sq_ft
FROM parcel_home ph
ORDER BY ph.property_id
LIMIT :limit;
