# Feature conventions

## Avoid duplicated behavior

- **Do not** add a new endpoint or SQL feature when the same data can be derived from an existing response.
- **Do** add summary/aggregate fields to the existing response when they belong with that data (e.g. `comp_count`, `confidence_band` on each F1 comp row).
- **Do** build derived UI (e.g. confidence message, badges) in the frontend or Tableau from existing API responses when possible.

Example: confidence summary is derived from F1 comps (first row’s `comp_count` and `confidence_band`); there is no separate confidence-only endpoint.
