-- Property info from mls_history: latest sale row for one property_id, with address (zip, city).
-- Parameters: :property_id
-- Uses property_id filter in all branches so indexes (mls_history.property_id, property_address.property_id) apply.

SELECT
  h.id AS sale_id,
  h.property_id,
  h.sold_date,
  h.sold_price,
  h.living_sq_ft,
  (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) AS ppsf,
  h.days_on_market,
  h.year_built,
  h.property_use_standardized,
  a.zip_code,
  c.name AS city_name
FROM mls_history h
LEFT JOIN (
  SELECT DISTINCT ON (property_id) property_id, street_id, zip_code
  FROM property_address
  WHERE property_id = :property_id
  ORDER BY property_id, street_id
) a ON a.property_id = h.property_id
LEFT JOIN street s ON s.id = a.street_id
LEFT JOIN city c ON c.id = s.city_id
WHERE h.property_id = :property_id
  AND h.sold_price > 0
  AND h.living_sq_ft > 0
  AND h.sold_date IS NOT NULL
ORDER BY h.sold_date DESC
LIMIT 1;
