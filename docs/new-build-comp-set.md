# New-build comp set (since 2020)

We use **comps of new homes built in the last five or six years, since 2020** as the benchmark for pricing. New builds sell at a premium, so this is the right comp set for valuing a new-build product.

**Rule:** If there are **no new homes being sold** in an area, that’s a **negative signal** – the area may not be a strong target for new-build.

---

## Where it’s used

- **New-build benchmark** (`NewBuildBenchmarkParams`, `new_build_benchmark()`): `min_sold_date="2020-01-01"`, `min_year_built=2020`. Returns p25/p50/p75 PPSF and DOM by area (ZIP × year) for sales with `year_built >= 2020` and `sold_date >= 2020-01-01`.
- **Rebuild eval**: New-build pricing (newbuild_p50_ppsf, newbuild_comp_count, has_newbuild) uses this benchmark. `has_newbuild = False` when no new-build comps exist → negative pricing signal.
- **Target pipeline summary**: Aggregates “new-build value” using median new-build PPSF by ZIP from the same benchmark (since 2020).
- **Feasibility / rebuild params**: `min_year_built` default is 2020 for new-build benchmark lookups.

---

## Defaults

| Parameter       | Default       | Meaning |
|----------------|---------------|--------|
| `min_sold_date`| `2020-01-01`  | Only sales on or after this date. |
| `min_year_built` | `2020`     | Only homes with year_built ≥ 2020 (last 5–6 years). |

API callers can override these (e.g. `POST /decisions/new-build-benchmark` with different `min_year_built` / `min_sold_date` if needed).
