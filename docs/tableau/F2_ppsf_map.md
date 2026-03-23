# PPSF map by ZIP (use ranked zips or ppsf-map)

There is **no F2 endpoint**. For a PPSF map by ZIP:

- **Ranked ZIPs (Week 1):** Use `POST /queries/ranked-zips-ppsf`. You get zip_code, median_ppsf, avg_living_sqft, sale_count. Use for a ZIP-level map; derive confidence from sale_count in a calculated field (<20 low, <50 med, else high).
- **With analytics:** Use `POST /queries/ppsf-map` with geography=zip or geography=grid for grid cells with centroid_lon/lat.

See `docs/features/F2_review.md`.
