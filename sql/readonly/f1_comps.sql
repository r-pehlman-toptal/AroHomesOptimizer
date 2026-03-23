-- F1 Comps: parameterized for FastAPI and Tableau. One row per comp; comp_count and confidence_band on every row.
-- Parameters: :zip_code, :min_sold_date, :max_sold_date, :filter_by_year_built (1 = filter by year_built, 0 = by sold_date), :min_year_built, :max_year_built, :limit, :ppsf_min, :city_name
-- Zip: compare as trimmed text. City: when :city_name is null or blank, do not filter by city.

WITH
addr_one AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id, a.street_id, a.zip_code
  FROM property_address a
  WHERE TRIM(CAST(a.zip_code AS TEXT)) = TRIM(CAST(:zip_code AS TEXT))
  ORDER BY a.property_id, a.street_id
),
street_city AS (
  SELECT s.id AS street_id, c.name AS city_name
  FROM street s
  JOIN city c ON c.id = s.city_id
),
base AS (
  SELECT
    h.id AS sale_id,
    h.property_id,
    h.sold_date,
    h.sold_price,
    h.living_sq_ft,
    (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) AS ppsf,
    a.zip_code,
    sc.city_name,
    h.year_built
  FROM mls_history h
  JOIN addr_one a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) >= :ppsf_min
    AND (TRIM(COALESCE(CAST(:city_name AS TEXT), '')) = '' OR UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name)))
    AND TRIM(CAST(a.zip_code AS TEXT)) = TRIM(CAST(:zip_code AS TEXT))
    AND (
      (:filter_by_year_built = 1 AND h.year_built >= :min_year_built AND h.year_built <= :max_year_built)
      OR
      (:filter_by_year_built = 0 AND h.sold_date >= :min_sold_date AND h.sold_date <= :max_sold_date)
    )
),
cohort AS (
  SELECT
    COUNT(DISTINCT sale_id)::int AS comp_count,
    CASE
      WHEN COUNT(DISTINCT sale_id) < 20 THEN 'low'
      WHEN COUNT(DISTINCT sale_id) < 50 THEN 'med'
      ELSE 'high'
    END AS confidence_band
  FROM base
)
SELECT
  b.sale_id,
  b.property_id,
  b.sold_date,
  b.sold_price,
  b.living_sq_ft,
  b.ppsf,
  b.zip_code,
  b.city_name,
  b.year_built,
  c.comp_count,
  c.confidence_band
FROM base b
CROSS JOIN cohort c
ORDER BY b.sold_date DESC
LIMIT :limit;
