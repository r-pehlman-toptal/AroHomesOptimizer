CREATE OR REPLACE VIEW analytics.v_f2_ppsf_map_zip AS
SELECT
  zip_code AS geo_id,
  NULL::double precision AS centroid_lon,
  NULL::double precision AS centroid_lat,
  sale_year,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ppsf) AS median_ppsf,
  AVG(ppsf) AS avg_ppsf,
  COUNT(*)::int AS comp_count,
  CASE
    WHEN COUNT(*) < 20 THEN 'low'
    WHEN COUNT(*) < 50 THEN 'med'
    ELSE 'high'
  END AS confidence_band
FROM analytics.mv_sale_la_since2020_ppsf400
WHERE zip_code IS NOT NULL
GROUP BY zip_code, sale_year;
