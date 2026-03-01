CREATE OR REPLACE VIEW analytics.v_f5_confidence_coverage_zip AS
SELECT
  zip_code AS geo_id,
  sale_year,
  COUNT(*)::int AS comp_count,
  CASE
    WHEN COUNT(*) < 20 THEN 'low'
    WHEN COUNT(*) < 50 THEN 'med'
    ELSE 'high'
  END AS confidence_band,
  'zip' AS geography_used,
  4 AS effective_tier,
  'zip' AS effective_geometry_type
FROM analytics.mv_sale_la_since2020_ppsf400
WHERE zip_code IS NOT NULL
GROUP BY zip_code, sale_year;
