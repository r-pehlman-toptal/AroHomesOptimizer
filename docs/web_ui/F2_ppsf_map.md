# PPSF map (use ranked zips or ppsf-map)

There is **no F2 endpoint**. For a PPSF map:

- **ZIP-level:** Call `POST /queries/ranked-zips-ppsf` (Week 1). Use zip_code + median_ppsf for the map; derive confidence_band in the UI from sale_count.
- **Grid or ZIP with analytics:** Call `POST /queries/ppsf-map` with geography=zip or grid. Grid returns centroid_lon/lat for map layers.

See `docs/features/F2_review.md`.
