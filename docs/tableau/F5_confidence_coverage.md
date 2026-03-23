# Confidence summary (from F1 comps)

There is **no separate F5 endpoint**. Use **F1 comps** and derive the summary in Tableau:

- Each F1 row has **comp_count** and **confidence_band** (same for all rows in the result).
- Use the first row (or any row) to show: "Based on N comps. Confidence: [band]."
- Optional: build a message with a calculated field, e.g. when comp_count < 20 show "Consider wider geography."

See **F1_comps.md** for the F1 SQL and parameters.
