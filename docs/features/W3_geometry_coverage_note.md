# W3 Feature: Geometry coverage note

## Delivered

| Item | Location |
|------|----------|
| **Note** | `notes/geometry-coverage-note.md` — metrics (total parcels, valid center_point %, SRID), risks |
| **Script** | `scripts/check_geometry_coverage.py` — run when DB available to refresh stats |

## Behavior

- Documents % of parcels with valid center_point and SRID consistency for parcel_gold / property_geometry.
- Run `python scripts/check_geometry_coverage.py` to print coverage and SRIDs.

## References

- Week 3 report: `docs/week3-report.md` §2.3
