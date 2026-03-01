"""
Query Service layer
-------------------

Productionized, parameterized read-only queries against Postgres for:

- LA bed/bath distribution (A)
- Principal detached-SFR zone per city (B)
- Lot size width/depth buckets by ZIP (C)
- Ranked ZIPs by PPSF with trimming and sample thresholds (D)
- Week 2: Comps (F1), offer range (F3), overpay risk (F4); PPSF map via ranked-zips-ppsf or ppsf-map

All queries are written using SQLAlchemy `text()` with bind parameters only.
Week 2 queries use analytics schema (mv_sale_la_since2020_ppsf400, grid, etc.).
"""

