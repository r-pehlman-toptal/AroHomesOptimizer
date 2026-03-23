-- Comps aggregate: hard filters + soft weights, then group-level aggregates.
-- OPTIMIZED: spatial-first (nearby_geom limits rows), then join mls_history; no full-table geom/addr scan.
-- Parameters: subject_parcel_id, subject_sqft, property_subtype, distance_cap_miles, size_band_pct, recency_months, ppsf_min, half_life_months, half_life_miles, city_name.

WITH subject_point AS (
  SELECT ST_Transform(pg.center_point::geometry, 3310) AS point_3310
  FROM property_geometry pg
  WHERE pg.property_id = :subject_parcel_id
    AND pg.center_point IS NOT NULL
    AND ST_IsValid(pg.center_point::geometry)
  LIMIT 1
),
-- Only geometries within distance cap (uses spatial index if present).
nearby_geom AS (
  SELECT
    pg.property_id,
    ST_Transform(pg.center_point::geometry, 3310) AS point_3310
  FROM property_geometry pg
  CROSS JOIN subject_point sp
  WHERE pg.center_point IS NOT NULL
    AND ST_IsValid(pg.center_point::geometry)
    AND ST_DWithin(ST_Transform(pg.center_point::geometry, 3310), sp.point_3310, 1609.34 * :distance_cap_miles)
),
-- Addresses only for nearby properties (not full table).
addr_nearby AS (
  SELECT DISTINCT ON (a.property_id)
    a.property_id, a.street_id, a.zip_code
  FROM property_address a
  WHERE a.property_id IN (SELECT property_id FROM nearby_geom)
  ORDER BY a.property_id, a.street_id
),
street_city AS (
  SELECT s.id AS street_id, c.name AS city_name
  FROM street s
  JOIN city c ON c.id = s.city_id
),
comps AS (
  SELECT
    h.id AS sale_id,
    h.property_id,
    h.sold_date,
    h.sold_price,
    h.living_sq_ft,
    (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) AS ppsf,
    h.days_on_market,
    (ST_Distance(g.point_3310, sp.point_3310) / 1609.34)::numeric AS dist_miles,
    (EXTRACT(year FROM age(current_date, h.sold_date))::int * 12
     + EXTRACT(month FROM age(current_date, h.sold_date))::int)::numeric AS months_ago
  FROM mls_history h
  JOIN nearby_geom g ON g.property_id = h.property_id
  JOIN addr_nearby a ON a.property_id = h.property_id
  JOIN street_city sc ON sc.street_id = a.street_id
  CROSS JOIN subject_point sp
  WHERE h.sold_price > 0
    AND h.living_sq_ft > 0
    AND h.sold_date IS NOT NULL
    AND h.sold_date <= current_date
    AND h.sold_date >= current_date - (interval '1 month' * :recency_months)
    AND (h.sold_price::numeric / NULLIF(h.living_sq_ft, 0)) >= :ppsf_min
    AND (:property_subtype IS NULL OR h.property_use_standardized = :property_subtype)
    AND h.property_id != :subject_parcel_id
    AND h.living_sq_ft BETWEEN :subject_sqft * (1 - :size_band_pct) AND :subject_sqft * (1 + :size_band_pct)
    AND UPPER(TRIM(sc.city_name)) = UPPER(TRIM(:city_name))
),
scored AS (
  SELECT
    *,
    (exp(-months_ago / :half_life_months) * exp(-dist_miles / :half_life_miles))::numeric AS w
  FROM comps
)
SELECT
  COUNT(*)::int AS comp_count,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ppsf) AS p25_ppsf,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ppsf) AS p75_ppsf,
  (PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ppsf) - PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ppsf))::numeric AS iqr_ppsf,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY days_on_market) AS median_dom,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY days_on_market) AS p75_dom,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY dist_miles) AS median_dist_miles,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY months_ago) AS median_months_ago,
  (COUNT(*) FILTER (WHERE dist_miles <= 0.25)::float / NULLIF(COUNT(*), 0) * 100)::numeric AS pct_within_025mi,
  (COUNT(*) FILTER (WHERE dist_miles <= 0.5)::float / NULLIF(COUNT(*), 0) * 100)::numeric AS pct_within_05mi,
  (COUNT(*) FILTER (WHERE months_ago <= 3)::float / NULLIF(COUNT(*), 0) * 100)::numeric AS pct_within_3mo,
  (COUNT(*) FILTER (WHERE months_ago <= 6)::float / NULLIF(COUNT(*), 0) * 100)::numeric AS pct_within_6mo,
  (COUNT(*) FILTER (WHERE living_sq_ft BETWEEN :subject_sqft * 0.8 AND :subject_sqft * 1.2)::float / NULLIF(COUNT(*), 0) * 100)::numeric AS pct_within_20pct_sqft
FROM scored;
