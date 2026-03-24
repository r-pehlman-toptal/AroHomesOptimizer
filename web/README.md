# Web visualizations (comps + aggregates)

Single-page app that implements the [visualization ladder](../docs/tableau/visualization_ladder.md) in the browser.

## What’s included

1. **F1 Comps** – Table of comps + PPSF histogram (ZIP, year, limit).
2. **ZIP × Year** – Bar chart (median PPSF by ZIP, filter by year) + line (median PPSF by year for one ZIP).
3. **City × Year** – Line charts: median PPSF over time and sales volume over time (multi-city).
4. **ZIP × Month** – Line: median PPSF and sale count by month (optional ZIP filter).
5. **PPSF Map** – Grid (0.25‑mi) points on a dark map; color by median PPSF, tooltip comp count.

## How to run

1. Start the API (with DB and env configured):
   ```bash
   uvicorn src.api.main:app --reload
   ```
2. Open in the browser:
   - **http://localhost:8000/app** or **http://localhost:8000/viz** (redirects to `/app`)
   - Or **http://localhost:8000/web/** to serve from the static mount.

All charts call the same-origin API (`/queries/...`). If the query router uses auth (e.g. Cognito), configure the client or temporarily relax auth for local use.

## Testing address lookup and rebuild eval

1. Open **http://localhost:8000/app** (or `/viz`).
2. Go to the **Rebuild** tab.
3. In the **Rebuild eval (address → feasibility + comps)** card:
   - **Address or property ID**: enter a numeric property ID (e.g. one that exists in your DB, like `12345`) or, for non-numeric text, also fill **ZIP** so the lookup can narrow results.
   - **ZIP (optional)**: use when the address text is not a property ID (e.g. street name) to limit candidates.
   - **Target size (sq ft)**: default 2700; used for feasibility and comps price band.
   - Click **Run rebuild eval**.
4. The result shows: resolved property ID and address, `is_valid`, notes, feasibility (max GFA, fits target?), and comps economics (price band, comp count, confidence). If the address cannot be resolved or the parcel has no geometry/zoning, you’ll see `is_valid: No` and notes explaining why.

## Stack

- Vanilla JS, no build step.
- [Chart.js](https://www.chartjs.org/) (CDN) for bar/line/histogram.
- [Leaflet](https://leafletjs.com/) (CDN) for the PPSF map.
- Dark theme; layout is responsive.
