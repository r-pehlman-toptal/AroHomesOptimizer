-- F1 Comps: PRODUCTION MODE (run by DBA when CREATE is allowed)
-- Prerequisites: analytics schema + mv_sale_la_since2020_ppsf400 exist (run 001, 010, 020).
-- This view adds cohort-level comp_count and confidence_band to the fact MV.
-- Tableau and API then filter by zip_code, sale_year and LIMIT in the query.

-- Optional: create view for F1 comps (zip + year cohort stats attached to each row)
CREATE OR REPLACE VIEW analytics.v_f1_comps AS
WITH cohort AS (
  SELECT
    zip_code,
    sale_year,
    COUNT(*)::int AS comp_count,
    CASE
      WHEN COUNT(*) < 20 THEN 'low'
      WHEN COUNT(*) < 50 THEN 'med'
      ELSE 'high'
    END AS confidence_band
  FROM analytics.mv_sale_la_since2020_ppsf400
  WHERE zip_code IS NOT NULL
  GROUP BY zip_code, sale_year
)
SELECT
  s.sale_id,
  s.property_id,
  s.sold_date,
  s.sold_price,
  s.living_sq_ft,
  s.ppsf,
  s.zip_code,
  s.city_name,
  s.year_built,
  c.comp_count,
  c.confidence_band
FROM analytics.mv_sale_la_since2020_ppsf400 s
JOIN cohort c ON c.zip_code = s.zip_code AND c.sale_year = s.sale_year
WHERE s.zip_code IS NOT NULL;

-- mv_sale_la_since2020_ppsf400: ix_mv_sale_la_since2020_ppsf400_zip_year (zip_code, sale_year)
-- No additional indexes required for v_f1_comps (it is a view over the indexed MV).

-- Refresh approach
-- The view reads from mv_sale_la_since2020_ppsf400. Refresh that MV on your cadence, e.g.:
--   REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_sale_la_since2020_ppsf400;
-- See scripts/refresh_mvs.py for order and options.
