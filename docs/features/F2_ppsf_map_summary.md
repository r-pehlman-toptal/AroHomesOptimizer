# F2 PPSF map — Deprecated (use Week 1 ranked zips or ppsf_map)

F2 has been **removed** from the API. Use:

- **ZIP-level PPSF map:** `POST /queries/ranked-zips-ppsf` (Week 1). Returns zip_code, median_ppsf, avg_living_sqft, sale_count. Derive confidence_band in the UI from sale_count (<20 low, <50 med, else high).
- **With analytics (grid or ZIP):** `POST /queries/ppsf-map` with geography=zip or grid for median_ppsf, comp_count, confidence_band (grid includes centroid_lon/lat).

See `docs/features/F2_review.md` for the comparison. F2 SQL files in `sql/readonly/` and production view remain optional for direct use if needed.
