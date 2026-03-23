# W3 Feature: Proximity to essentials

## Delivered

| Item | Location |
|------|----------|
| **Read-only SQL** | `sql/readonly/parcel_center_point.sql` (parameter: `:parcel_id`) |
| **Endpoint** | `POST /queries/parcel-center` — returns parcel_id, longitude, latitude (WGS84) |
| **Distance helper** | `src/feasibility/proximity.py` — `distance_km()`, `distances_to_pois()`, `nearest_poi_stub()` |
| **Usage** | Get parcel center via API; pass to external POI service or use distances_to_pois() with app-provided POI list. |

## Behavior

- **Parcel center:** Use `POST /queries/parcel-center` with parcel_id to get lon/lat. Empty if no valid geometry.
- **Distance:** `proximity.distances_to_pois((lon, lat), [(label, lon, lat), ...])` returns list of (label, distance_km). Haversine approximation.
- **Stub:** `nearest_poi_stub(parcel_id, poi_type)` returns message that external POI is required.

## External POI

Groceries, hospitals, parks are not in the DB. Integrate with a POI API or static layer; use parcel center + `distances_to_pois()` once POI coordinates are available.

## References

- Geometry coverage: `notes/geometry-coverage-note.md`, `scripts/check_geometry_coverage.py`
