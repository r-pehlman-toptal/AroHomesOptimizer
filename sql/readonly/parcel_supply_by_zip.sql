-- Parcel supply count per ZIP that meet lot requirements (min width, depth, area).
-- Read-only; for product→where-to-build supply estimates.
-- Parameters: :min_width_ft, :min_depth_ft, :min_lot_sq_ft, :city_name.

WITH addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id, a.street_id, a.zip_code
  FROM property_address a
  ORDER BY a.property_id, a.street_id
),
street_city AS (
  SELECT s.id AS street_id, c.name AS city_name
  FROM street s
  JOIN city c ON c.id = s.city_id
),
eligible AS (
  SELECT a.zip_code
  FROM property_geometry pg
  JOIN addr_one a ON a.property_id = pg.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE pg.vendor_lot_width_ft IS NOT NULL
    AND pg.vendor_lot_depth_ft IS NOT NULL
    AND pg.vendor_lot_width_ft >= :min_width_ft
    AND pg.vendor_lot_depth_ft >= :min_depth_ft
    AND COALESCE(pg.lot_size_sq_ft, pg.vendor_lot_width_ft * pg.vendor_lot_depth_ft) >= :min_lot_sq_ft
    AND UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name))
    AND a.zip_code IS NOT NULL
)
SELECT zip_code AS geo_id, COUNT(*)::int AS supply_count
FROM eligible
GROUP BY zip_code
ORDER BY supply_count DESC;
