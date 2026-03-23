# F1 Comps selection + display — Summary

## Delivered

| Item | Location |
|------|----------|
| **Read-only SQL** (single SELECT, no CREATE) | `sql/readonly/f1_comps.sql` |
| **FastAPI endpoint** | `POST /queries/f1/comps` |
| **Request model** | `F1CompsParams`: zip_code, sale_year=2024, limit=10, min_comps=30, ppsf_min=400 |
| **Response model** | `F1CompsRow`: sale_id, property_id, sold_date, sold_price, living_sq_ft, ppsf, zip_code, city_name, year_built, comp_count, confidence_band |
| **Tableau instructions** | `docs/tableau/F1_comps.md` |
| **Web UI plan** | `docs/web_ui/F1_comps.md` |
| **Production-mode SQL** | `sql/production/f1_comps_production.sql` (view + notes) |

## Parameters (all parameterized)

- **sale_year** — default 2024  
- **min_comps** — default 30 (used for UI warning when cohort &lt; min_comps)  
- **ppsf_min** — default 400  
- **zip_code** — required  
- **limit** — default 10, max 50  

## Tableau

- Connect to Postgres; run the read-only SQL as Custom SQL (or equivalent).
- Bind parameters: sale_year, zip_code, limit, ppsf_min.
- Map fields as in `docs/tableau/F1_comps.md`.

## Web app

- Call `POST /queries/f1/comps` with JSON body.
- Render table + summary card + low-sample warning as in `docs/web_ui/F1_comps.md`.

## Production upgrade (when DBA has CREATE)

- Run `sql/production/f1_comps_production.sql` to create `analytics.v_f1_comps`.
- API/Tableau can then query the view with `WHERE zip_code = ? AND sale_year = ? ORDER BY sold_date DESC LIMIT ?` for better performance (uses indexed MV).
