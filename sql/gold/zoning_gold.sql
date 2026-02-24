-- Canonical parcel-level zoning attributes.
-- This is where LA-specific zoning + overlays should be normalized.

CREATE OR REPLACE VIEW zoning_gold AS
SELECT
    z.parcel_id,
    z.zone_code,
    z.height_limit_ft,
    z.max_far,
    z.min_lot_size_sqft,
    z.front_setback_ft,
    z.side_setback_ft,
    z.rear_setback_ft,
    z.parking_ratio,
    z.overlay_codes
FROM staging_zoning AS z;

