# Web UI plan: F3 Offer range

## One screen

**Name:** Recommended offer range

**Purpose:** User enters ZIP and living sqft; app shows low/base/high offer (p25/p50/p75 PPSF × sqft).

## Inputs

| Input        | Type   | Default | Notes   |
|-------------|--------|--------|--------|
| ZIP code    | Text   | —      | Required |
| Living sq ft| Number | —      | Required, > 0 |
| Sale year   | Number | 2024   |         |
| PPSF min    | Number | 400    | Optional |

## API call

- **POST** `/queries/f3/offer-range`
- **Body:** `{"zip_code": "90012", "living_sq_ft": 1500, "sale_year": 2024, "ppsf_min": 400}`
- **Response:** One-element array with `low_ppsf`, `base_ppsf`, `high_ppsf`, `low_price`, `base_price`, `high_price`, `comp_count`, `geography_used`. Empty array if no comps.

## Output rendering

1. **Cards:** Three cards — Low (low_price), Base (base_price), High (high_price). Optional: show PPSF values (low_ppsf, base_ppsf, high_ppsf).
2. **Footer:** "Based on {comp_count} comps in ZIP {zip} for {year}. Geography: {geography_used}."
3. **Empty state:** If `[]`, show "No comps for this ZIP and year."
