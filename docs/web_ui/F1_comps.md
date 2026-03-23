# Web UI plan: F1 Comps selection + display

## One screen

**Screen name:** Comps by ZIP

**Purpose:** User enters a ZIP and optional year/limit; the app shows a table of comparable sales and a short confidence message.

## Inputs

| Input        | Type   | Default | Validation      | Notes                    |
|-------------|--------|---------|-----------------|--------------------------|
| ZIP code    | Text   | —       | Required, non-empty | Trim whitespace          |
| Sale year   | Number | 2024    | 2020 ≤ year     |                          |
| Max comps   | Number | 10      | 1–50            | How many rows to show    |
| Min comps   | Number | 30      | ≥ 1             | Used only for warning    |

Optional: **PPSF min** (default 400) as advanced input; most users keep default.

## API call

- **Method:** POST  
- **URL:** `/queries/f1/comps`  
- **Body (JSON):**
  ```json
  {
    "zip_code": "90012",
    "sale_year": 2024,
    "limit": 10,
    "min_comps": 30,
    "ppsf_min": 400
  }
  ```
- **Response:** JSON array of comp rows; each row has `sale_id`, `property_id`, `sold_date`, `sold_price`, `living_sq_ft`, `ppsf`, `zip_code`, `city_name`, `year_built`, `comp_count`, `confidence_band`.

## Output rendering

1. **Summary card (above table)**  
   - One line: “Showing up to N comps for ZIP {zip} in {year}. Cohort size: {comp_count} sales (confidence: {confidence_band}).”  
   - If `comp_count` < `min_comps`: add warning: “Low sample size — consider a wider area or different year.”

2. **Table**  
   - Columns: Sold date, Sold price, Living sq ft, PPSF, City, Year built.  
   - Sort by sold date descending (API already returns in this order).  
   - Optional: color or badge for `confidence_band` (e.g. low = amber, med = blue, high = green).

3. **Empty state**  
   - If response is `[]`: “No comps found for this ZIP and year. Try another ZIP or year.”

## Minimal layout (sketch)

```
[ ZIP code: [____] ] [ Sale year: [2024] ] [ Max comps: [10] ] [ Get comps ]

Cohort: 42 comps for 90012 in 2024 (confidence: high).

| Sold date   | Sold price | Living sq ft | PPSF   | City       | Year built |
|-------------|------------|--------------|--------|------------|------------|
| 2024-01-15  | 1,200,000  | 1,850        | 648.65 | LOS ANGELES| 1962       |
...
```

## No map in F1

F1 is table-only. Map (e.g. by lat/lon) can be added later when production-mode views with grid are available.
