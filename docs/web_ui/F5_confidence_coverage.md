# Confidence summary (from F1 comps)

There is **no separate F5 endpoint**. When you show comps per ZIP (F1), add the summary in the UI with a small function:

- Call **POST /queries/f1/comps** with zip_code, sale_year, etc.
- From the response, take the **first row** (or any row): it has **comp_count** and **confidence_band**.
- Build the message in the frontend, e.g.:
  - `comp_count < 20` → "ZIP has N comps; below 20. Consider wider geography."
  - `comp_count < 50` → "Based on N comps. Confidence: medium."
  - else → "Based on N comps. Confidence: high."

Display that as a badge or text card next to the comps table. No extra API call.
