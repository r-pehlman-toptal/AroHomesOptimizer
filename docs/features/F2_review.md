# F2 PPSF map — Review: is it needed?

## What F2 does

- **Read-only** ZIP-level PPSF map: one row per ZIP with `geo_id`, `median_ppsf`, `avg_ppsf`, `comp_count`, `confidence_band` (centroid_lon/lat are NULL).
- Filters: LA city, 2020+, one `sale_year`, `ppsf_min` 400.

## What you already have (more advanced)

| Source | What it does | Compared to F2 |
|--------|----------------|----------------|
| **Week 1: ranked_zips_ppsf** (`POST /queries/ranked-zips-ppsf`) | ZIPs with **median_ppsf**, **avg_living_sqft**, **sale_count**; ranked by median_ppsf; county (LA/Orange), SFR, PPSF trim, min_sale_count. | Same idea: ZIP + median PPSF for a map. **sale_count** = comp_count; **confidence_band** can be derived in UI from sale_count (<20 low, <50 med, else high). No `sale_year` (uses min_sold_date). |
| **Week 2: ppsf_map** (`POST /queries/ppsf-map`, analytics) | **Grid (0.25-mi) or ZIP** with median_ppsf, avg_ppsf, comp_count, confidence_band; grid has **centroid_lon/lat**. | Strictly more advanced when analytics exists: same ZIP view plus **grid** with real geometry. |

## Conclusion

- **F2 is not required** for this project:
  - For a **ZIP-level PPSF map**, use **ranked_zips_ppsf** (Week 1): you get zip_code + median_ppsf + sale_count; derive confidence_band in the UI from sale_count.
  - When you have **analytics**, use **ppsf_map** (grid or zip) for a proper map (including grid centroids).
- F2 duplicates “ZIP + median_ppsf + comp_count” that ranked_zips_ppsf already provides, with the only extra being a single **sale_year** filter and **avg_ppsf**. If you need year-specific ZIP PPSF in read-only mode, you could add an optional `sale_year` to ranked_zips_ppsf instead of keeping a separate F2.

**Recommendation:** Remove F2 (endpoint, schemas, SQL, docs) and use ranked_zips_ppsf for ZIP PPSF map; use ppsf_map when analytics is available.
