# Week 2 verification steps

Run these after deploying gold and (optionally) analytics SQL. Requires `DB_URL` in `.env`.

## 1. Apply gold views

**Option A – script (recommended):**

```bash
# From project root, with DB_URL set in .env or environment
python scripts/apply_gold.py
```

This runs `sql/gold/parcel_gold.sql`, `sql/gold/transaction_gold.sql`, and `sql/agg/city_year.sql` in order.

**Option B – psql:**

```bash
psql "$DB_URL" -f sql/gold/parcel_gold.sql
psql "$DB_URL" -f sql/gold/transaction_gold.sql
psql "$DB_URL" -f sql/agg/city_year.sql
```

## 2. Gold row-count and uniqueness tests

```bash
# Run after applying gold (step 1). Skips automatically if DB_URL is not set or connection fails.
pytest tests/test_row_counts.py -v
```

## 3. Analytics serving layer (optional)

Run in order:

```bash
psql "$DB_URL" -f sql/001_create_schema.sql
psql "$DB_URL" -f sql/010_v_fact_sale_clean.sql
psql "$DB_URL" -f sql/020_mv_sale_la_since2020_ppsf400.sql
psql "$DB_URL" -f sql/030_mv_agg_city_year_metrics.sql
psql "$DB_URL" -f sql/040_grid_cells_025.sql
psql "$DB_URL" -f sql/041_populate_grid_cells_025.sql
psql "$DB_URL" -f sql/050_mv_agg_grid_year_ppsf_025.sql
# If using tier views:
psql "$DB_URL" -f sql/055_grid_year_tiers_fallback.sql
```

Then refresh MVs:

```bash
python scripts/refresh_mvs.py --concurrently true
# Optional: repopulate grid cells
python scripts/refresh_mvs.py --concurrently true --refresh-grid true
```

## 4. Sanity queries

- `SELECT COUNT(*), COUNT(DISTINCT parcel_id) FROM parcel_gold;` — counts should match.
- `SELECT COUNT(*), COUNT(DISTINCT transaction_id) FROM transaction_gold;` — counts should match.
- Query Tableau or API for `mv_agg_city_year_metrics` and `mv_agg_grid_year_ppsf_025` to confirm serving layer is usable.
