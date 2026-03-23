# W3 Feature: ADU feasibility check

## Delivered

| Item | Location |
|------|----------|
| **Stub** | `src/feasibility/adu.py` — `check_adu_feasibility()`, `ADUFeasibilityResult` |
| **Usage** | Call with parcel_id (and optional zone_code, lot_size_sq_ft); display status and message in UI. |

## Behavior

- **Stub:** Returns `status="stub"` and message that LA ADU rules are not yet in DB/code.
- **Future:** Replace with rule-based logic using zone, lot size, setbacks, existing GFA/units when LA ADU rules are defined.

## References

- Zoning sources: `docs/zoning-source-and-field-mapping.md` (ADU documented as Phase 2 / stub)
