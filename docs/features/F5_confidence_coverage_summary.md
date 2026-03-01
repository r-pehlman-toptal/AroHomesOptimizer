# F5 Confidence + coverage — Deprecated (use F1)

Confidence summary is **not a separate endpoint**. When you show comps per ZIP (F1), add the summary in the UI:

- **comp_count** and **confidence_band** are on every F1 row (same value for the cohort).
- From the first row (or any row), use `comp_count` and `confidence_band` to build a message, e.g.:
  - `comp_count < 20` → "ZIP has N comps; below 20. Consider wider geography."
  - `comp_count < 50` → "Based on N comps. Confidence: medium."
  - else → "Based on N comps. Confidence: high."

No F5 API; no separate SQL for confidence-only. The F5 SQL files in `sql/readonly/` and `sql/production/` remain optional for direct Tableau use if you ever want a single-query summary without loading comp rows.
