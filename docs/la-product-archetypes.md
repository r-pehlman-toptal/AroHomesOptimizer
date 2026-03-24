# LA product archetypes (Week 4)

**Purpose:** Propose 3–4 unit mixes/size bands to focus optimization and design recommendations on. These archetypes are used in Week 5+ for baseline models and constraint-based optimization.

---

## 1. Archetype list

| # | Archetype | Unit mix | Size band (living sq ft) | Typical zoning | Use |
|---|-----------|----------|---------------------------|----------------|-----|
| 1 | **SFR standard** | 1 unit | 1,200–2,800 | R1, RS, RE | Primary single-family; majority of LA suburban stock. |
| 2 | **SFR plus ADU** | 1 + 1 ADU | Main 1,200–2,500; ADU 300–1,200 | R1, RS (ADU permitted) | Incremental density; rental or family. |
| 3 | **Small multifamily (2–4)** | 2–4 units | 600–1,400 per unit | R2, R3 | Duplex/triplex/fourplex; infill and small lots. |
| 4 | **Multifamily (5–8)** | 5–8 units | 500–1,200 per unit | RM, R4 | Small apartment; higher-density corridors. |

---

## 2. Rationale

- **SFR standard** aligns with existing comps (SINGLE FAMILY RESIDENCE), PPSF and DOM baselines, and R1/RS/RE zoning.
- **SFR plus ADU** uses the same lot envelope with an additional permitted unit; feasibility and economics depend on ADU rules (stub in Week 3).
- **2–4 unit** and **5–8 unit** cover small multifamily and RM-style product; zoning constraints (max_units, parking) drive feasibility; optimization can target unit mix and size bands within these ranges.

---

## 3. How they are used

- **Week 5:** Feature tables and baseline PPSF/DOM models can be stratified by archetype (or property_use) where data allows.
- **Optimization:** Constraint-based design (e.g. in `src/models/design_optimization.py`) can use these as candidate unit mixes and size bands; zoning (max_units, max_gfa_estimate) and lot dimensions constrain feasibility.
- **Dashboards:** Submarket PPSF and DOM can be broken down by typology (SFR vs 2–4 vs 5+) when the data has property_use or unit count.

---

## 4. References

- [docs/week4-plan.md](week4-plan.md) – Week 4 features and handoff to Week 5.
- [src/feasibility/zoning_constraints.py](../src/feasibility/zoning_constraints.py) – max_units, max_gfa by zone.
- [docs/features/W3_adu_feasibility.md](features/W3_adu_feasibility.md) – ADU stub.
