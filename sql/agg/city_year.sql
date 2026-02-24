-- City-year aggregates for scenario analysis.

CREATE OR REPLACE VIEW city_year AS
SELECT
    p.city,
    DATE_PART('year', t.close_date) AS year,
    COUNT(*) AS transaction_count,
    AVG(t.price_per_sqft) AS avg_price_per_sqft,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t.price_per_sqft) AS median_price_per_sqft,
    AVG(t.days_on_market) AS avg_days_on_market,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t.days_on_market) AS median_days_on_market
FROM transaction_gold AS t
JOIN parcel_gold AS p
    ON t.parcel_id = p.parcel_id
GROUP BY
    p.city,
    DATE_PART('year', t.close_date);

