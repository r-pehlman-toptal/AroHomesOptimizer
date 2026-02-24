-- Analytics tables for Market Expansion dashboards.
-- These can be applied directly or translated into Alembic migrations.

CREATE TABLE IF NOT EXISTS analytics_regression_runs (
    id                  BIGSERIAL PRIMARY KEY,
    scope               TEXT NOT NULL,              -- e.g. 'county_wide', 'target_markets'
    market_name         TEXT,                       -- e.g. 'westside', 'hollywood_pasadena'
    geo_filter          JSONB,                      -- counties, cities, zips
    property_filters    JSONB,                      -- typology, year built, etc.
    date_range_start    DATE,
    date_range_end      DATE,
    coef_sqft           NUMERIC,                    -- coefficient for delta_sqft
    intercept           NUMERIC,                    -- intercept
    r_squared           NUMERIC,
    sample_size         INTEGER NOT NULL,
    notes               TEXT,
    params              JSONB,                      -- full parameter snapshot for reproducibility
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          TEXT
);


CREATE TABLE IF NOT EXISTS analytics_home_size_scenarios (
    id                  BIGSERIAL PRIMARY KEY,
    regression_run_id   BIGINT NOT NULL REFERENCES analytics_regression_runs(id) ON DELETE CASCADE,
    scope               TEXT NOT NULL,
    market_name         TEXT,
    size_sqft           INTEGER NOT NULL,
    non_zero_count      INTEGER NOT NULL,
    total_value         NUMERIC NOT NULL,
    avg_non_zero_value  NUMERIC NOT NULL,
    config              JSONB,                      -- scenario-specific config (costs, margins, etc.)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_home_size_scenarios_run_id
    ON analytics_home_size_scenarios (regression_run_id, size_sqft);


CREATE TABLE IF NOT EXISTS analytics_lot_heatmap (
    id                      BIGSERIAL PRIMARY KEY,
    scope                   TEXT NOT NULL,
    market_name             TEXT,
    geo_unit_type           TEXT NOT NULL,          -- 'zip', 'city', 'county'
    geo_unit_value          TEXT NOT NULL,
    width_bucket_ft         INTEGER,                -- nullable if only lot_size bucket used
    depth_bucket_ft         INTEGER,
    lot_size_bucket_sqft    INTEGER,
    lot_count               INTEGER NOT NULL,
    missing_geom_count      INTEGER NOT NULL DEFAULT 0,
    params                  JSONB,                  -- bucket size, filters, etc.
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lot_heatmap_scope_geo
    ON analytics_lot_heatmap (scope, market_name, geo_unit_type, geo_unit_value);


CREATE TABLE IF NOT EXISTS analytics_value_maps (
    id                          BIGSERIAL PRIMARY KEY,
    scope                       TEXT NOT NULL,
    market_name                 TEXT,
    geo_unit_type               TEXT NOT NULL,      -- 'zip', 'city', etc.
    geo_unit_value              TEXT NOT NULL,
    estimated_value_median      NUMERIC NOT NULL,
    estimated_value_per_sf_med  NUMERIC NOT NULL,
    sample_size                 INTEGER NOT NULL,
    params                      JSONB,              -- filters, regression run id, date range
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_value_maps_scope_geo
    ON analytics_value_maps (scope, market_name, geo_unit_type, geo_unit_value);

