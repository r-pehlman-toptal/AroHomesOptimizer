# W3 Feature: Nearby zoning display

## Delivered

| Item | Location |
|------|----------|
| **Read-only SQL** | `sql/readonly/nearby_zoning.sql` (parameters: `:parcel_id`, `:limit`) |
| **Endpoint** | `POST /queries/nearby-zoning` |
| **Request** | `NearbyZoningParams`: parcel_id (subject), limit (default 21 = subject + 20 nearby) |
| **Response** | `NearbyZoningRow`: parcel_id, zip_code, zone_code, is_subject |

## Behavior

- Returns zoning for the subject parcel (is_subject=true) plus other parcels in the same ZIP, from property_zoning + zone. Subject row first, then others by parcel_id.
- Use to show "Subject: R1" and "Nearby: R1, R2, R1, …" in UI.

## References

- Data map: `docs/data-map.md` (property_zoning, zone)
