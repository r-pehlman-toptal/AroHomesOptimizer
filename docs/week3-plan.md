# Week 3 Plan – Zoning and feasibility foundations

**Project:** Aro Homes – LA Market Expansion (Data-Driven Design)  
**Period:** Week 3 of 8  
**Scope:** LA zoning sources, constraint-ready fields, first feasibility module, geometry coverage.

---

## 1. Objectives

- **Understand LA zoning sources:** Gather zoning/planning docs or existing zoning layers; identify FAR, height, lot coverage, setbacks, parking.
- **Translate zoning into constraint-ready fields:** Map sources to fields usable for feasibility (e.g. max GFA, height, parking, units).
- **Implement first feasibility module:** `ZoningConstraintBuilder` in `src/feasibility/` that joins parcel + zoning + geometry and outputs a constraints DataFrame/table (placeholder or real `max_gfa_estimate`, `max_height_ft`, `min_parking_spaces`, `max_units`).
- **Validate geometry coverage:** Check % parcels with valid `center_point` or `perimeter`; SRID consistency; document in a short geometry-coverage note.

---

## 2. Prerequisites (from Week 2)

- Gold views (`parcel_gold`, `transaction_gold`) and data map for join paths and keys.
- Serving-layer MVs (city×year, grid×year) available for later submarket definitions.
- Read-only API (F1, F3, F4) in place; no duplicate endpoints; conventions in `docs/features/CONVENTIONS.md`.

---

## 3. Tasks and deliverables

| Task | Deliverable |
|------|-------------|
| Gather LA zoning/planning docs or existing zoning layers; identify FAR, height, lot coverage, setbacks, parking | **Zoning source list and field mapping** |
| Implement first version of `ZoningConstraintBuilder` in `src/feasibility/`: join parcel + zoning + geometry; output placeholder or real `max_gfa_estimate`, `max_height_ft`, `min_parking_spaces`, `max_units` | **Feasibility module** that produces a constraints DataFrame/table |
| Check geometry: % parcels with valid `center_point` or `perimeter`; SRID consistency | **Short geometry-coverage note** |
| Write Week 3 report | **Week 3 report** (e.g. `docs/week3-report.md`) |

---

## 4. Features (8) – Week 3 scope

| # | Feature | Notes |
|---|---------|--------|
| 1 | **Zoning summary ("what you can build")** | From zone + ZoningConstraintBuilder once populated. |
| 2 | **Explainable comps ("why these comps")** | Short text: same cell/zip, same year, similar size. |
| 3 | **Inspection questions by year built** | App logic driven by year_built from parcel/MLS. |
| 4 | **Proximity to essentials** | Use center_point + external POI (groceries, hospitals, parks) for distance. |
| 5 | **Setback/height/FAR summary** | Once zoning detail or feasibility is in place. |
| 6 | **ADU feasibility check** | Stub or rule-based once LA zoning rules are in DB/code. |
| 7 | **Nearby zoning display** | Show zone(s) for subject and nearby parcels from property_zoning + zone. |
| 8 | **Geometry coverage note** | % parcels with valid center_point; SRID consistency (aligns with geometry check above). |

---

## 5. Acceptance

- One feasibility script runs for a subset of LA and produces a constraints table.
- Zoning mapping (sources → fields) is documented.
- Geometry-coverage note exists (valid center_point %, SRID).
- Week 3 report is written.

---

## 6. Handoff to Week 4

- Feasibility constraints table and ZoningConstraintBuilder feed feature tables for modeling (Week 5).
- Zoning and geometry coverage inform submarket and archetype work (Week 4).
- Features (8) above are either implemented as stubs/documentation or deferred with a clear note.

---

*Update as work completes; save final state in `docs/week3-report.md`.*
