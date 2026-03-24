-- New-build benchmark: PPSF and DOM for comp set of new homes built in last 5–6 years (since 2020).
-- New builds sell at a premium; no new builds in an area is a negative signal.
-- Parameters: :min_sold_date (e.g. 2020-01-01), :min_year_built (e.g. 2020), :city_name, optional :zip_code.

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
    sc.city_name,
    EXTRACT(YEAR FROM h.sold_date)::int AS sale_year,
    (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) AS ppsf,
    h.days_on_market
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date IS NOT NULL
    AND h.sold_date >= :min_sold_date
    AND h.year_built >= :min_year_built
    AND (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) >= 400
    AND UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name))
    AND (:zip_code IS NULL OR a.zip_code = :zip_code)
)
SELECT
  zip_code,
  city_name,
  sale_year,
  COUNT(*)::int AS sale_count,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ppsf)::float AS p25_ppsf,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf)::float AS median_ppsf,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ppsf)::float AS p75_ppsf,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY days_on_market)::float AS p25_dom,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_on_market)::float AS median_dom,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY days_on_market)::float AS p75_dom
FROM base
GROUP BY zip_code, city_name, sale_year
ORDER BY zip_code, sale_year;
