# Comps + aggregates visualization ladder (Tableau / BI)

Use this as the single reference for building comp and aggregate views. For each view: **what it answers**, **best chart**, and **exact fields** for X / Y / Color / Size / Tooltip / Filters. Data sources point to repo SQL and analytics MVs.

---

## 1) F1 Comps / comps-aggregate rows (row-level) — “Show me the evidence”

**Data source:**  
- **F1 (ZIP + year):** `POST /queries/f1/comps` or `sql/readonly/f1_comps.sql` → `sale_id`, `sold_date`, `sold_price`, `living_sq_ft`, `ppsf`, `zip_code`, `city_name`, `year_built`, `comp_count`, `confidence_band`.  
- **Comps aggregate (subject + 12mo + distance):** `POST /queries/comps-aggregate-rows` or `sql/readonly/comps_aggregate_rows.sql` → same sale fields + **`dist_miles`**, **`months_ago`**, **`w`**. Add **`days_on_market`** if in your query; address from address tables if joined.

### A) Table (first view)

| What it answers | What are the actual comps? |
|-----------------|-----------------------------|
| **Chart**       | Table                      |
| **Columns**     | `sold_date`, `sold_price`, `living_sq_ft`, `ppsf`, `days_on_market` (if available), `dist_miles` (comps-aggregate only), address (if joined) |
| **Filters**     | subtype (`property_use_standardized`), last 12 months, distance/radius, size band (set in API params for comps-aggregate) |

### B) Scatter: PPSF vs distance

| What it answers | Are far comps distorting pricing? |
|-----------------|------------------------------------|
| **Chart**       | Scatter                            |
| **X**           | `dist_miles`                       |
| **Y**           | `ppsf`                             |
| **Color**       | `months_ago` or `sold_date`        |
| **Size**        | `sold_price` or `living_sq_ft`     |
| **Reference**   | Horizontal line at **median_ppsf** (from comps-aggregate response or aggregate row) |

*Use comps-aggregate-rows so you have `dist_miles` and `months_ago`.*

### C) Histogram: PPSF distribution

| What it answers | What’s the price band and spread? |
|-----------------|-----------------------------------|
| **Chart**       | Histogram (bar)                   |
| **X**           | `ppsf` (binned)                   |
| **Y**           | Count of comps                   |
| **Overlay**     | Reference lines at **p25_ppsf**, **p50_ppsf** (median), **p75_ppsf** from comps-aggregate |

---

## 2) ZIP × Year aggregate — “What’s typical in this ZIP (this year)?”

**Data source:** `sql/readonly/volume_by_zip_year.sql` → `zip_code`, `sale_year`, **`sale_count`**, **`median_ppsf`**, **`median_dom`**. For p25/p75 by ZIP×year add a separate query or extend the SQL.

### A) Bar: Median PPSF by ZIP

| What it answers | Which ZIPs are expensive/cheap? |
|-----------------|----------------------------------|
| **Chart**       | Bar                              |
| **X**           | `zip_code`                       |
| **Y**           | `median_ppsf`                    |
| **Color**       | `confidence_band` or comp-count tier (derive from `sale_count`, e.g. &lt;20 low, &lt;50 med, else high) |
| **Tooltip**     | `sale_count`, `p25_ppsf` / `p75_ppsf` (if available), `median_dom` |
| **Filter**      | `sale_year` (e.g. 2024)          |

### B) Line: Median PPSF by year (one ZIP)

| What it answers | Trend (up/down)? |
|-----------------|------------------|
| **Chart**       | Line             |
| **X**           | `sale_year`      |
| **Y**           | `median_ppsf`    |
| **Filter**      | `zip_code`       |
| **Tooltip**     | `sale_count`, `median_dom` |

---

## 3) City × Year aggregate — “Macro trend sanity check”

**Data source:** `analytics.mv_agg_city_year_metrics` (after `scripts/refresh_mvs.py`) → `city_id`, **`sale_year`**, **`city_name`**, `total_revenue`, **`total_sales`**, `avg_ppsf`, **`median_ppsf`**.

### A) Line: Median PPSF over time (multi-city)

| What it answers | City-level trend and market regime shifts |
|-----------------|------------------------------------------|
| **Chart**       | Line                                     |
| **X**           | `sale_year`                              |
| **Y**           | `median_ppsf`                            |
| **Color**       | `city_name`                              |
| **Tooltip**     | `total_sales`, `avg_ppsf` (median_dom not in MV; add from fact if needed) |

### B) Line: Sales volume over time

| What it answers | Liquidity cycles and thin-market risk |
|-----------------|----------------------------------------|
| **Chart**       | Line                                    |
| **X**           | `sale_year`                             |
| **Y**           | `total_sales` (sales count)              |
| **Color**       | `city_name`                             |
| **Tooltip**     | `median_ppsf`, `total_sales`             |

---

## 4) Grid (0.25‑mile) × Year aggregate — “Micro-market heatmap”

**Data source:**  
- Aggregates: `analytics.mv_agg_grid_year_ppsf_025` → **`cell_id`**, **`sale_year`**, **`comp_count`**, **`median_ppsf`**, `avg_ppsf`, `new_comp_count`, **`confidence_band`**.  
- Geometry: `analytics.grid_cells_025` → **`cell_id`**, **`geom_3310`** (polygon), **`centroid_lon`**, **`centroid_lat`** (WGS84 for point maps).  
Join on `cell_id`. For Tableau polygon map, use `geom_3310` (may need export as WKT/GeoJSON or spatial connection); for point map use `centroid_lon`, `centroid_lat`.

### A) Map heatmap (must-have)

| What it answers | Where are the expensive pockets and boundaries? |
|-----------------|-------------------------------------------------|
| **Chart**       | Map (polygon grid cells or centroid points)      |
| **Mark**        | Polygon (grid cell) or point (centroid_lon, centroid_lat) |
| **Color**       | `median_ppsf`                                   |
| **Opacity / Filter** | `comp_count >=` threshold (e.g. 10 or 20)  |
| **Tooltip**     | `comp_count`, `median_ppsf`, `confidence_band`, `sale_year` |
| **Filter**      | `sale_year`                                     |

### B) Map: Confidence overlay

| What it answers | Where are we guessing? |
|-----------------|------------------------|
| **Chart**       | Map (same geometry as above) |
| **Color**       | `confidence_band` (low / med / high) |
| **Label (optional)** | `comp_count`              |
| **Tooltip**     | `comp_count`, `median_ppsf`, `confidence_band` |

**Tip:** Build two map sheets (Price vs Confidence) and use a dashboard toggle to switch between them.

---

## 5) ZIP × Month aggregate (optional) — “Seasonality”

**Data source:** `sql/readonly/volume_by_zip_month.sql` → `zip_code`, **`sale_month`** (date, first of month), **`sale_count`**, **`median_ppsf`**, **`median_dom`**.  
Derive **month_of_year** (1–12) or **month-year** from `sale_month` for axes.

### A) Line: Monthly median PPSF (one ZIP)

| What it answers | Seasonality / timing |
|-----------------|----------------------|
| **Chart**       | Line                 |
| **X**           | `sale_month` or month-year |
| **Y**           | `median_ppsf`        |
| **Filter**      | `zip_code`           |
| **Optional**    | Second line or dual axis: `sale_count` (volume) |

### B) Heatmap: Month-of-year vs ZIP

| What it answers | Which ZIPs spike in spring/summer? |
|-----------------|------------------------------------|
| **Chart**       | Heatmap (matrix)                   |
| **Rows**        | `zip_code`                         |
| **Columns**     | `month_of_year` (1–12 from `sale_month`) |
| **Color**       | `median_ppsf` or `sale_count`     |
| **Filter**      | `sale_year` (or range of years)    |

---

## Quick reference: data sources

| View / level        | Source (SQL or MV)                          | Key fields |
|---------------------|---------------------------------------------|------------|
| F1 comps (rows)     | `f1_comps.sql` / F1 API                    | sold_date, sold_price, living_sq_ft, ppsf, comp_count, confidence_band |
| Comps aggregate rows| `comps_aggregate_rows.sql` / comps-aggregate-rows API | + dist_miles, months_ago, w, days_on_market |
| Comps aggregate (1 row) | `comps_aggregate.sql` / comps-aggregate API | comp_count, median_ppsf, p25/p75, iqr_ppsf, median_dom, diagnostics, confidence_score, confidence_band |
| ZIP × Year          | `volume_by_zip_year.sql`                    | zip_code, sale_year, sale_count, median_ppsf, median_dom |
| ZIP × Month         | `volume_by_zip_month.sql`                  | zip_code, sale_month, sale_count, median_ppsf, median_dom |
| City × Year         | `analytics.mv_agg_city_year_metrics`       | city_name, sale_year, total_sales, median_ppsf |
| Grid × Year         | `analytics.mv_agg_grid_year_ppsf_025` + `analytics.grid_cells_025` | cell_id, sale_year, comp_count, median_ppsf, confidence_band, centroid_lon/lat, geom_3310 |

---

## SQL checklist (implemented one by one)

| Ladder view        | SQL / object in repo | Use in Tableau |
|--------------------|----------------------|----------------|
| **1) F1 comps (rows)** | `sql/readonly/f1_comps.sql` | **Yes** — parameterized (`:zip_code`, `:sale_year`, `:limit`, `:ppsf_min`). API uses this. |
| | `sql/readonly/f1_comps_tableau.sql` | Optional: with lat/lon; edit literals. |
| | `sql/readonly/f1_comps_executable.sql` | Optional: edit zip, year, limit, ppsf_min. |
| **2) ZIP × Year** | `sql/readonly/volume_by_zip_year.sql` | Parameterized `:min_sold_date`, `:zip_code`. |
| | `sql/readonly/volume_by_zip_year_executable.sql` | **Yes** — paste and run (default from 2020, all ZIPs). |
| **3) City × Year** | `sql/readonly/volume_by_city_year.sql` | **Yes** — read-only from public tables; params `:min_sold_date`, `:city_name`. |
| | `sql/readonly/volume_by_city_year_executable.sql` | **Yes** — paste and run (LA from 2020). |
| | `analytics.mv_agg_city_year_metrics` | If analytics schema exists: run `030_mv_agg_city_year_metrics.sql`, then `SELECT * FROM analytics.mv_agg_city_year_metrics`. |
| **4) Grid × Year** | `sql/readonly/tableau_grid_year.sql` | **Yes** — single query joining grid + MV. Requires analytics schema and grid/MV built (040, 041, 050 or `scripts/refresh_mvs.py`). Param: optional `:sale_year`. |
| **5) ZIP × Month** | `sql/readonly/volume_by_zip_month.sql` | Parameterized `:min_sold_date`, `:zip_code`. |
| | `sql/readonly/volume_by_zip_month_executable.sql` | **Yes** — paste and run (default from 2020). |
| **Comps aggregate** | `sql/readonly/comps_aggregate.sql`, `comps_aggregate_rows.sql` | For subject-based comps with distance/recency weights; use via API or bind params. |

All ladder views now have at least one ready-to-use SQL in `sql/readonly/` (parameterized or executable). City × Year and Grid × Year also have executable or single-query options.
