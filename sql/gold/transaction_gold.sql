-- transaction_gold: one row per MLS sale for aggregates and modeling.
-- Source: mls_history. Joins to parcel_gold via parcel_id = property_id.
-- Spec: one row per transaction; price, DOM, PPSF, beds/baths, living_sq_ft. Data map: docs/data-map.md.

CREATE OR REPLACE VIEW transaction_gold AS
SELECT
  h.id AS transaction_id,
  h.property_id AS parcel_id,
  h.sold_date AS close_date,
  h.sold_price AS sale_price,
  h.living_sq_ft,
  h.bedrooms_total AS beds,
  h.bathrooms_full + COALESCE(h.bathrooms_half, 0) * 0.5 AS baths,
  h.days_on_market,
  h.property_use_standardized AS property_type,
  h.year_built,
  -- Derived
  (h.sold_price / NULLIF(h.living_sq_ft, 0))::numeric AS price_per_sqft
FROM mls_history h
WHERE h.sold_date IS NOT NULL
  AND h.sold_price > 0
  AND h.living_sq_ft > 0;

COMMENT ON VIEW transaction_gold IS 'One row per MLS sale (mls_history.id). parcel_id=property_id for join to parcel_gold. price_per_sqft, days_on_market for city_year.';
