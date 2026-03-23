-- Volume and liquidity by ZIP × year (Tableau/BI). Edit :min_sold_date or :zip_code if needed.
-- Default: all LA ZIPs from 2020; bind parameters in Tableau or use literals below.

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
base AS (
  SELECT
    a.zip_code,
    EXTRACT(YEAR FROM h.sold_date)::int AS sale_year,
    h.sold_price,
    (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) AS ppsf,
    h.days_on_market
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date IS NOT NULL
    AND h.sold_date >= DATE '2020-01-01'
    AND UPPER(TRIM(sc.city_name)) = 'LOS ANGELES'
)
SELECT
  zip_code,
  sale_year,
  COUNT(*)::int AS sale_count,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_on_market) AS median_dom
FROM base
GROUP BY zip_code, sale_year
ORDER BY zip_code, sale_year;
