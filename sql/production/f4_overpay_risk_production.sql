CREATE OR REPLACE VIEW analytics.v_f4_overpay_risk_zip AS
SELECT
  zip_code,
  sale_year,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
  COUNT(*)::int AS comp_count,
  'zip' AS geography_used
FROM analytics.mv_sale_la_since2020_ppsf400
WHERE zip_code IS NOT NULL
GROUP BY zip_code, sale_year;
