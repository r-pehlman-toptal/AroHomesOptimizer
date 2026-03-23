# W3 Feature: Explainable comps ("why these comps")

## Delivered

| Item | Location |
|------|----------|
| **Helper** | `src/query_service/explain_comps.py` — `explain_comps_text()` |
| **Usage** | Call with F1 (or F3/F4) response context; display in UI. |

## Behavior

- **Input:** geography_used (e.g. "zip" or "cell"), sale_year, comp_count, optional zip_code, optional living_sq_ft.
- **Output:** Short text, e.g. "Same ZIP (90012), same year (2024), similar size (subject 2,100 sq ft). 42 comparable sale(s) in this cohort."

## Usage

From F1 comps response: take first row’s `comp_count`, `confidence_band`; use request `zip_code`, `sale_year`; optionally subject `living_sq_ft`. Then:

```python
from src.query_service.explain_comps import explain_comps_text

msg = explain_comps_text(
    geography_used="zip",
    sale_year=2024,
    comp_count=42,
    zip_code="90012",
    living_sq_ft=2100,
)
# Display msg in UI.
```

No new endpoint; derive from existing F1 (and F3/F4) responses.
