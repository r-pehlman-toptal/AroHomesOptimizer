-- Canonical transaction / listing table.
-- One row per listing_id or transaction_id with standardized measures.

CREATE OR REPLACE VIEW transaction_gold AS
SELECT
    t.transaction_id,
    t.listing_id,
    t.parcel_id,
    t.close_date,
    t.list_price,
    t.sale_price,
    t.days_on_market,
    t.beds,
    t.baths,
    t.living_sqft,
    t.lot_sqft,
    t.property_type,
    t.submarket,
    -- Derived measures
    CASE
        WHEN t.living_sqft > 0 THEN t.sale_price / t.living_sqft
        ELSE NULL
    END AS price_per_sqft
FROM staging_transactions AS t;

