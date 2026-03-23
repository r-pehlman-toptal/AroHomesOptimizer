-- Approximate "homes added to the market" in Los Angeles: count of sales where
-- inferred list date (sold_date - days_on_market) falls in the period.
-- Requires: mls_history.sold_date, mls_history.days_on_market (integer or numeric).
-- Parameters: :period_start (date), :period_end (date), :city_name (e.g. LOS ANGELES).

WITH addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id, a.street_id
  FROM property_address a
  ORDER BY a.property_id, a.street_id
),
street_city AS (
  SELECT s.id AS street_id, c.name AS city_name
  FROM street s
  JOIN city c ON c.id = s.city_id
),
with_inferred_list_date AS (
  SELECT
    h.id AS sale_id,
    h.property_id,
    h.sold_date,
    h.days_on_market,
    (h.sold_date - (COALESCE(h.days_on_market, 0)::int * interval '1 day'))::date AS inferred_list_date
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE h.sold_date IS NOT NULL
    AND h.sold_price > 0
    AND h.living_sq_ft > 0
    AND UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name))
)
SELECT
  COUNT(*)::int AS homes_added_count
FROM with_inferred_list_date
WHERE inferred_list_date >= :period_start
  AND inferred_list_date <= :period_end;
