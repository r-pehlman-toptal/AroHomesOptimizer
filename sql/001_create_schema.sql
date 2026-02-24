-- 001_create_schema.sql
-- Creates analytics schema and enables PostGIS + required extensions.
-- Run once per database. Safe to re-run (IF NOT EXISTS).

CREATE SCHEMA IF NOT EXISTS analytics;

-- PostGIS for geometry and spatial indexing (EPSG:3310 California Albers, distance/grid work).
CREATE EXTENSION IF NOT EXISTS postgis;

-- Optional: trigram for fuzzy text (e.g. city name fallback). Uncomment if needed.
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;

COMMENT ON SCHEMA analytics IS 'Serving layer for LA residential pricing: clean fact view, filtered MVs, city/year and grid/year aggregates.';
