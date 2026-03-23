# Submarket definition (Week 4)

**Purpose:** Define canonical geographies for LA market analysis, dashboards, and modeling. Submarkets are used for PPSF comparison, exploratory charts, and coverage-by-geography.

---

## 1. Canonical geographies

We use **two** canonical geographies for submarket-level analysis:

| Geography | Definition | Source | Use |
|-----------|------------|--------|-----|
| **City** | Municipal boundary (city name from address/city_id). | `parcel_gold.city`, `transaction_gold`; `analytics.mv_agg_city_year_metrics` | City × year: median PPSF, DOM, volume. Submarket PPSF comparison across LA cities. |
| **Grid (0.25-mile)** | Hex or square grid cell (402 m) in EPSG:3310. | `analytics.grid_cells_025`, `analytics.mv_agg_grid_year_ppsf_025` | Grid × year: comp_count, median_ppsf, new_comp_count, confidence_band. Map and tiered fallback (0.25-mi → 3×3 → 5×5 → ZIP → city). |

**Neighborhood** (macro/micro) is not yet defined; can be added later as a named list or polygon layer (e.g. community plan areas, ZIP clusters).

---

## 2. Submarket list (city-level)

For “submarket” in the sense of **named areas to compare**, we treat each **city** as a submarket. The following are in scope for LA market expansion (aligned with web UI city dropdown and data). Machine-readable list: **`data/submarkets.yaml`** (canonical_geographies: city, grid_025mi; cities: list).

- LOS ANGELES  
- BURBANK  
- GLENDALE  
- PASADENA  
- SANTA MONICA  
- LONG BEACH  
- INGLEWOOD  
- CULVER CITY  
- WEST HOLLYWOOD  
- SAN FERNANDO  

Aggregates: use `analytics.mv_agg_city_year_metrics` (city_id, city_name, sale_year, total_sales, median_ppsf, avg_ppsf) or read-only `volume_by_city_year` / `volume_by_zip_year` where applicable.

---

## 3. Grid as submarket

Each **0.25-mile cell** is a geographic submarket for map-based analysis. Metrics per (cell_id, sale_year):

- `comp_count`, `median_ppsf`, `avg_ppsf`, `new_comp_count`, `confidence_band`  
- From `analytics.mv_agg_grid_year_ppsf_025`.  
- Join `analytics.grid_cells_025` for centroid_lat, centroid_lon, geom_3310.

For “where we have enough comps,” use **tiered fallback**: `analytics.v_grid_year_effective_tier` (effective_tier 1–5, effective_comp_count ≥ 20).

---

## 4. Typology (SFR vs small multifamily)

Submarket comparison can be split by **property use** (e.g. SFR vs small multifamily) using:

- `transaction_gold` / fact MV with `property_use_standardized` or equivalent.  
- Filter or group by use (e.g. SINGLE FAMILY RESIDENCE, 2–4 unit, 5+ unit) for exploratory charts and modeling.

Typology is not a separate geography; it is a dimension applied within city or grid.

---

## 5. References

- [docs/week4-plan.md](week4-plan.md) – Week 4 tasks and features.  
- [docs/serving-layer-README.md](serving-layer-README.md) – analytics schema, city×year, grid×year, tier views.  
- [sql/agg/city_year.sql](../sql/agg/city_year.sql) – city × year view from gold.  
- [sql/agg/grid_year.sql](../sql/agg/grid_year.sql) – grid × year view over analytics MV (when present).
