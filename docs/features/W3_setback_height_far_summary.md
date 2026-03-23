# W3 Feature: Setback/height/FAR summary

## Delivered

| Item | Location |
|------|----------|
| **Source** | `POST /queries/zoning-summary` (zone_code, max_gfa_estimate, max_height_ft, min_parking_spaces, max_units) |
| **Formatter** | `src/feasibility/constraint_summary.py` — `format_setback_height_far_summary()` |
| **Usage** | Call formatter with zoning-summary response (and optional setbacks when in lookup/staging). |

## Behavior

- **Data:** Zoning summary endpoint already returns max_gfa_estimate (FAR × lot), max_height_ft, min_parking_spaces, max_units. Setbacks (front/side/rear) are documented in `docs/zoning-source-and-field-mapping.md`; add to zone lookup or staging_zoning when available.
- **Formatter:** Produces one-line text, e.g. "Zone R1. Max GFA ~2,500 sq ft. max height 30 ft. 2.0 parking min. up to 1 unit(s). Setbacks: front 20 ft, side 5 ft, rear 20 ft."

## References

- Zoning summary: `docs/features/W3_zoning_summary.md`
- Zoning sources: `docs/zoning-source-and-field-mapping.md`
