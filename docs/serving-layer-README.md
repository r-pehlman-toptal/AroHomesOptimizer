# LA Residential Pricing – Serving Layer (Postgres/PostGIS)

Production-ready **analytics** schema: one-row-per-sale fact, filtered LA fact MV, city×year and 0.25-mile grid×year aggregates for **Tableau and API**, with indexes and refresh scripts.

---

## Assumptions

- **Source tables (public or your schema):**
  - `mls_history`: `id` (sale_id), `property_id`, `sold_date`, `sold_price`, `living_sq_ft`, `property_use_standardized`, optionally `year_built`
  - `property_address`: `property_id`, `street_id` (optionally `is_primary`, `updated_at`)
  - `street`: `id`, `city_id`
  - `city`: `id`, `name` (and optionally `county`)
  - `property_geometry`: `property_id`, `center_point` (geometry Point, 4326) or `geom`
- **Location filter (LA):** Implemented as `UPPER(TRIM(city_name)) = 'LOS ANGELES'`. To use a boundary polygon instead, add a table e.g. `la_boundary (geom)` and in `010_v_fact_sale_clean.sql` replace the city filter with `EXISTS (SELECT 1 FROM la_boundary lb WHERE ST_Intersects(point_4326, lb.geom))`.
- **PostGIS:** Extensions `postgis` required; grid and distance use **EPSG:3310** (California Albers). `point_3310` is stored on the fact MV to avoid repeated `ST_Transform` in spatial joins.
- **Secrets:** Not hardcoded; use env `DATABASE_URL` or `DB_URL` for the Python refresh script.

---

## Objects Created (schema `analytics`)

| Object | Type | Purpose |
|--------|------|--------|
| `v_fact_sale_clean` | View | One row per sale; no fan-out; LA only; `point_4326` / `point_3310` |
| `mv_sale_la_since2020_ppsf400` | MV | Filtered fact: sold_date ≥ 2020-01-01, ppsf ≥ 400, LA |
| `mv_agg_city_year_metrics` | MV | City × year: total_revenue, total_sales, avg_ppsf, median_ppsf |
| `grid_cells_025` | Table | 0.25-mile (402.336 m) grid in 3310; `cell_id`, `geom_3310`, centroid lat/lon |
| `mv_agg_grid_year_ppsf_025` | MV | Grid × year: comp_count, median_ppsf, avg_ppsf, new_comp_count, confidence_band |
| `v_zip_year_comp` | View | Zip × year comp counts (for tier-4 fallback) |
| `v_cell_year_primary_geo` | View | Per (cell_id, sale_year): mode zip and city of sales in that cell |
| `v_grid_year_comp_tiers` | View | Comp counts at tier 1 (0.25-mi) through 5 (city): comp_025, comp_3x3, comp_5x5, comp_zip, comp_city |
| `v_grid_year_effective_tier` | View | Effective tier (1–5) and effective_comp_count using min 20 comps; use to choose geography for inference |

---

## Indexes (why they exist)

- **mv_sale_la_since2020_ppsf400**
  - **UNIQUE (sale_id):** Required for `REFRESH MATERIALIZED VIEW CONCURRENTLY`.
  - **(sale_year), (city_id, sale_year), (sold_date):** Time and group-by filters for dashboards and Tableau.
  - **GIST (point_3310):** Spatial join to grid cells without transforming on the fly.
- **mv_agg_city_year_metrics**
  - **UNIQUE (city_id, sale_year):** Concurrent refresh.
  - **(sale_year):** Year-first filters.
- **mv_agg_grid_year_ppsf_025**
  - **UNIQUE (cell_id, sale_year):** Concurrent refresh.
  - **(sale_year):** Year filters.
- **grid_cells_025**
  - **GIST (geom_3310):** Fast point-in-polygon for grid×year join.
  - **(x_idx, y_idx):** Lookup by grid indices.

---

## How to Run

### 1. One-time setup (migrations)

Run in order (from project root, with `DB_URL` or `DATABASE_URL` set):

```bash
psql "$DB_URL" -f sql/001_create_schema.sql
psql "$DB_URL" -f sql/010_v_fact_sale_clean.sql
psql "$DB_URL" -f sql/020_mv_sale_la_since2020_ppsf400.sql
psql "$DB_URL" -f sql/030_mv_agg_city_year_metrics.sql
psql "$DB_URL" -f sql/040_grid_cells_025.sql
psql "$DB_URL" -f sql/050_mv_agg_grid_year_ppsf_025.sql
psql "$DB_URL" -f sql/055_grid_year_tiers_fallback.sql
```

If `property_geometry` uses `geom` instead of `center_point`, edit `010` and use `pg.geom` (and set SRID 4326 if needed). If `mls_history` has no `year_built`, remove it from the view and from the fact MV.

### 2. Refresh MVs (ongoing)

```bash
# Concurrent refresh (no lock on read; recommended)
python scripts/refresh_mvs.py --concurrently true

# Repopulate grid from current fact extent (e.g. after big data load)
python scripts/refresh_mvs.py --concurrently true --refresh-grid
```

Order: `mv_sale_la_since2020_ppsf400` → (optional grid repopulate) → `mv_agg_city_year_metrics` → `mv_agg_grid_year_ppsf_025`.

### 3. Optional: initial empty MVs then first refresh

To create MVs empty then fill once:

```sql
-- After 020 indexes exist:
CREATE MATERIALIZED VIEW analytics.mv_sale_la_since2020_ppsf400 WITH (fillfactor=100) AS
SELECT 1 WHERE false;
-- then create unique index, then:
REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_sale_la_since2020_ppsf400;
```

Same idea for the other MVs if you prefer empty-first. The provided 020/030/050 create populated MVs directly.

---

## Refresh cadence

- **Recommended:** Nightly or after MLS load (e.g. cron 02:00).
- **Concurrent:** Use `--concurrently true` so Tableau/API can keep reading while refresh runs.
- **Grid:** Run `--refresh-grid` only when extent or grid definition changes (e.g. weekly or after large backfill).

---

## Tiered comp fallback (sample size for inference)

For each 0.25-mile cell × year we expose comp counts at five tiers so you can decide where you have enough sample for inferences (and whether to widen from 0.25-mile):

1. **Tier 1:** 0.25-mile cell (`comp_025`).
2. **Tier 2:** 3×3 cells (~0.75-mile) (`comp_3x3`).
3. **Tier 3:** 5×5 cells (~1.25-mile) (`comp_5x5`).
4. **Tier 4:** ZIP (`comp_zip`; primary ZIP = mode of sales in that cell).
5. **Tier 5:** City (`comp_city`; primary city = mode of sales in that cell).

Query **`analytics.v_grid_year_effective_tier`** for a ready-made choice: it picks the first tier with comp count ≥ 20 and sets `effective_tier`, `effective_comp_count`, and `effective_geometry_type` (`'cell_025' | 'cell_3x3' | 'cell_5x5' | 'zip' | 'city'`). Use this to drive which geography you use for PPSF or other inferences. The threshold 20 is in the view definition; change it there if you want a different minimum.

---

## Tableau usage

- **City × year:** `analytics.mv_agg_city_year_metrics` — dimensions `city_id`, `city_name`, `sale_year`; measures `total_revenue`, `total_sales`, `avg_ppsf`, `median_ppsf`.
- **Grid × year:** `analytics.mv_agg_grid_year_ppsf_025` — join to `analytics.grid_cells_025` on `cell_id` for `geom_3310` or `centroid_lon`/`centroid_lat` for mapping; use `comp_count` and `confidence_band` for filtering or tooltips.
- **Map:** Use `grid_cells_025.centroid_lat`, `centroid_lon` for point maps, or `geom_3310` (Tableau 2022+ PostGIS) for polygons. For fact-level maps, use `mv_sale_la_since2020_ppsf400.point_4326` (WGS84) if your tool supports it.

---

## File list

| File | Purpose |
|------|--------|
| `sql/001_create_schema.sql` | Create `analytics` schema, enable PostGIS |
| `sql/010_v_fact_sale_clean.sql` | Base view: one row per sale, LA, no fan-out |
| `sql/020_mv_sale_la_since2020_ppsf400.sql` | Filtered fact MV + indexes |
| `sql/030_mv_agg_city_year_metrics.sql` | City × year MV + indexes |
| `sql/040_grid_cells_025.sql` | Grid table + populate from fact extent |
| `sql/041_populate_grid_cells_025.sql` | Repopulate grid (used by script with `--refresh-grid`) |
| `sql/050_mv_agg_grid_year_ppsf_025.sql` | Grid × year PPSF MV + indexes |
| `sql/055_grid_year_tiers_fallback.sql` | Tiered comp views (0.25-mi → 3×3 → 5×5 → ZIP → city) |
| `sql/090_refresh_concurrently.sql` | Example REFRESH CONCURRENTLY statements |
| `scripts/refresh_mvs.py` | Python refresh in dependency order, timings, `--concurrently` / `--refresh-grid` |
