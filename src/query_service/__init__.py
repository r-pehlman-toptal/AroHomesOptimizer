"""
Query Service layer
-------------------

Productionized, parameterized read-only queries against Postgres for:

- LA bed/bath distribution (A)
- Principal detached-SFR zone per city (B)
- Lot size width/depth buckets by ZIP (C)
- Ranked ZIPs by PPSF with trimming and sample thresholds (D)

All queries are written using SQLAlchemy `text()` with bind parameters only.
"""

