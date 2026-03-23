# W3 Feature: Inspection questions by year built

## Delivered

| Item | Location |
|------|----------|
| **Config** | `data/inspection_questions_by_year.yaml` — bands and question sets |
| **Module** | `src/feasibility/inspection_questions.py` — `get_inspection_questions()`, `get_inspection_band_label()` |
| **Usage** | App passes parcel_gold.year_built or MLS year_built; display returned questions in UI. |

## Behavior

- **get_inspection_questions(year_built)** returns a list of suggested inspection questions for that build year. Bands: Pre-1960, 1960–1978, 1979–1990, 1991–2010, 2011+. Default set when year_built is None or no band matches.
- **get_inspection_band_label(year_built)** returns the band label (e.g. "Pre-1960") for display.

## Config

YAML: `bands` (ordered; first match wins), each with `min_year`, `max_year`, `label`, `questions`; and `default.questions`. Optional dependency: PyYAML; if not installed, returns a single default question.

## References

- Parcel year_built: `parcel_gold.year_built`, `notes/parcel_gold_spec.md`
