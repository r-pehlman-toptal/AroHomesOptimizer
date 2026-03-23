# Number of Homes Added to the Market (Los Angeles)

## Can we calculate it?

**Approximation: yes**, with current data. **Exact: no**, without a real listing/list date.

## Current data

- **mls_history** has one row per **sale**: `sold_date`, `days_on_market`, address (via joins). There is **no** `list_date` or listing date column.

“Homes added to the market” usually means **new listings** in a period (date the home was listed). That would need a **list_date** (or equivalent) and would include homes still for sale or later delisted. We don’t have that.

## What we can do: inferred “list” date (sold homes only)

For each **sale** we can approximate when it came on the market as:

- **inferred_list_date = sold_date − days_on_market**

Then we **count sales** where that inferred date falls in the period and city = Los Angeles. So we get:

- **“Number of homes that came on the market (approx.) in LA in [period] and later sold.”**

That is a **proxy** for “homes added to the market” limited to homes that sold. We do **not** count listings that are still active or were withdrawn.

## SQL

- **`sql/readonly/homes_added_to_market_la.sql`**  
  Parameters: `:period_start`, `:period_end` (dates), optional `:city_name` (default LOS ANGELES).  
  Returns one row: `homes_added_count`.

Example (last 12 months in LA):

```sql
-- period_start = current_date - interval '12 months'
-- period_end   = current_date
-- city_name    = NULL (default LOS ANGELES)
```

## For a true “new listings” metric

- Add a **list_date** (or listing date) to the pipeline and schema (e.g. from MLS or listing feed).
- Then count rows where `list_date` is in the period and city = LA. That would be “Number of homes added to the market” including unsold/delisted.
