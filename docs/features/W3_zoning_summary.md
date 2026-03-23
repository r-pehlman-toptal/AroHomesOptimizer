# W3 Feature: Zoning summary ("what you can build")

## Delivered

| Item | Location |
|------|----------|
| **Read-only SQL** | `sql/readonly/zoning_summary.sql` (parameter: `:parcel_id`) |
| **FastAPI endpoint** | `POST /queries/zoning-summary` |
| **Request** | `ZoningSummaryParams`: parcel_id (required) |
| **Response** | `ZoningSummaryRow`: parcel_id, zone_code, lot_size_sq_ft, max_gfa_estimate, max_height_ft, min_parking_spaces, max_units |

## Behavior

- Looks up one parcel by `parcel_id` (property_id) from public tables: address → property_zoning → zone, and property_geometry for lot_size_sq_ft.
- Applies LA zone-code lookup (R1, R2, RS, RE, RM) to fill max_gfa_estimate (lot × FAR), max_height_ft, min_parking_spaces, max_units.
- Returns one row or empty list if parcel not found.

## Zone lookup

Aligned with `src/feasibility/zoning_constraints.DEFAULT_LA_ZONE_LOOKUP` and `_ZONE_LOOKUP` in `src/query_service/queries.py`. Replace with LAMC-derived or staging_zoning when available.

## References

- Zoning sources and field mapping: `docs/zoning-source-and-field-mapping.md`
- Feasibility module: `src/feasibility/zoning_constraints.py`
