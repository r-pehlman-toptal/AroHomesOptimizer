# Web UI plan: F4 Overpay risk

## One screen

**Name:** Overpay risk

**Purpose:** User enters list price, ZIP, living sqft; app shows comp-based value, % above comps, and risk level (low/medium/high).

## Inputs

| Input        | Type   | Notes     |
|-------------|--------|-----------|
| ZIP code    | Text   | Required  |
| List price  | Number | Required, > 0 |
| Living sq ft| Number | Required, > 0 |
| Sale year   | Number | Default 2024 |
| PPSF min    | Number | Default 400 |

## API call

- **POST** `/queries/f4/overpay-risk`
- **Body:** `{"zip_code": "90012", "list_price": 950000, "living_sq_ft": 1500, "sale_year": 2024, "ppsf_min": 400}`
- **Response:** One row: comp_median_ppsf, comp_based_value, list_price, pct_above_comps, risk_level, comp_count, geography_used. Empty list if no comps.

## Output rendering

1. **Card:** Comp-based value = $X (based on median PPSF × living sq ft).
2. **Card:** List price is **Y%** above/below comp-based value (show pct_above_comps; if negative, "below").
3. **Badge:** Risk level (low = green, medium = amber, high = red).
4. **Footer:** "Based on {comp_count} comps in ZIP {zip}."
