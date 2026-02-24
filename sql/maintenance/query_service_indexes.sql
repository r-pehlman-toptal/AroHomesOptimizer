-- Suggested indexes to support Query Service performance.

-- mls_history
CREATE INDEX IF NOT EXISTS idx_mls_history_use_sold_date
    ON mls_history (property_use_standardized, sold_date);

CREATE INDEX IF NOT EXISTS idx_mls_history_property_id
    ON mls_history (property_id);

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

