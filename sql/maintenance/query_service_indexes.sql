-- Suggested indexes to support Query Service performance.
-- Run: psql $DATABASE_URL -f sql/maintenance/query_service_indexes.sql
-- The spatial index (idx_property_geometry_center_3310) is critical for comps-aggregate; without it the query can take 40+ minutes.

-- mls_history
CREATE INDEX IF NOT EXISTS idx_mls_history_use_sold_date
    ON mls_history (property_use_standardized, sold_date);

CREATE INDEX IF NOT EXISTS idx_mls_history_property_id
    ON mls_history (property_id);

-- Helps v_fact_sale_clean + mv_sale_la refresh (filter sold_date >= '2020-01-01').
CREATE INDEX IF NOT EXISTS idx_mls_history_sold_date
    ON mls_history (sold_date);

-- property_address
CREATE INDEX IF NOT EXISTS idx_property_address_property_id
    ON property_address (property_id);

CREATE INDEX IF NOT EXISTS idx_property_address_street_id
    ON property_address (street_id);

CREATE INDEX IF NOT EXISTS idx_property_address_zip_code
    ON property_address (zip_code);

-- street and city
CREATE INDEX IF NOT EXISTS idx_street_city_id
    ON street (city_id);

CREATE INDEX IF NOT EXISTS idx_city_name_county
    ON city (name, county);

-- zoning
CREATE INDEX IF NOT EXISTS idx_property_zoning_property_id
    ON property_zoning (property_id);

CREATE INDEX IF NOT EXISTS idx_property_zoning_zone_id
    ON property_zoning (zone_id);

CREATE INDEX IF NOT EXISTS idx_zone_name
    ON zone (name);

-- For heavy ILIKE searches on zone.name, consider trigram index (requires pg_trgm extension):
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE INDEX IF NOT EXISTS idx_zone_name_trgm
--     ON zone USING gin (name gin_trgm_ops);

-- geometry
CREATE INDEX IF NOT EXISTS idx_property_geometry_property_id
    ON property_geometry (property_id);

-- Spatial index for comps-aggregate: ST_DWithin(transform(center_point), subject, radius).
-- Requires PostGIS. Speeds up comps-aggregate from minutes to seconds.
CREATE INDEX IF NOT EXISTS idx_property_geometry_center_3310
    ON property_geometry USING GIST (ST_Transform(center_point::geometry, 3310));

