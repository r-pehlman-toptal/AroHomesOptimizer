CREATE OR REPLACE VIEW analytics.v_f3_offer_range_zip AS
WITH zip_sales AS (
  SELECT zip_code, sale_year, ppsf
  FROM analytics.mv_sale_la_since2020_ppsf400
  WHERE zip_code IS NOT NULL
),
pct AS (
  SELECT
    zip_code,
    sale_year,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ppsf) AS p25,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ppsf) AS p75,
    COUNT(*)::int AS comp_count
  FROM zip_sales
  GROUP BY zip_code, sale_year
)
SELECT
  zip_code,
  sale_year,
  p25 AS low_ppsf,
  p50 AS base_ppsf,
  p75 AS high_ppsf,
  comp_count,
  'zip' AS geography_used
FROM pct;
