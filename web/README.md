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

## Stack

- Vanilla JS, no build step.
- [Chart.js](https://www.chartjs.org/) (CDN) for bar/line/histogram.
- [Leaflet](https://leafletjs.com/) (CDN) for the PPSF map.
- Dark theme; layout is responsive.
