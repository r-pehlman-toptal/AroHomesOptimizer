-- Canonical parcel-level table for LA residential optimization work.
-- One row per parcel_id, joined to assessor and geometry where available.

CREATE OR REPLACE VIEW parcel_gold AS
SELECT
    p.parcel_id,
    p.apn,
    p.city,
    p.neighborhood,
    p.zone_code,
    a.year_built,
    a.land_sqft,
    a.improvement_sqft,
    g.geom,            -- geometry column (database-specific type)
    g.centroid_lon,
    g.centroid_lat
FROM staging_parcels AS p
LEFT JOIN staging_assessor AS a
    ON p.apn = a.apn
LEFT JOIN staging_parcel_geom AS g
    ON p.parcel_id = g.parcel_id;

