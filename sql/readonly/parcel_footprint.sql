-- Parcel footprint: lot width, depth, area. Optional inferred fallback done in Python if columns exist.
-- Width = frontage (vendor_lot_width_ft), depth = lot depth (vendor_lot_depth_ft).
-- Parameters: :property_id
-- Returns one row per property; Python computes aspect_ratio, ratio_band, sources, is_valid_dimensions, notes.

SELECT
  pg.property_id,
  pg.lot_size_sq_ft,
  pg.vendor_lot_width_ft,
  pg.vendor_lot_depth_ft
FROM property_geometry pg
WHERE pg.property_id = :property_id
LIMIT 1;
