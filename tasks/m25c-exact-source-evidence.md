# M25C exact actor-to-citation and component/line source attempt

Status: **complete; no qualifying exact-date record; no remediation authorized**

Date: `2026-08-24`

## Scope

Obtain sources that could address the exact failure reasons on the remaining
107 actors, 206 rejected components, 180 pairs, and 32 finding routes. Preserve
the frozen IDs and prior hashes, and submit only records that independently
establish the relevant actor, target date, component coverage or shared line,
and usable lineage.

## Result

Eight new source candidates were checked with exact locators and explicit
date, geometry, access, and license dispositions. One new peer-reviewed source
was measurable record by record: Perreault's 2025 georeferenced digitization
of Driver et al.'s 1953 ethnolinguistic map of North and Central America.

The source improves traceability but not qualification:

| Surface | Frozen records | New complete or positive binding |
| --- | ---: | ---: |
| Actors | 107 | 32 complete named-feature bindings |
| Components | 206 | 74 with named polygon intersections |
| Pairs | 180 | 53 complete named-feature bindings on both sides |
| Finding routes | 32 | 0 qualifying exact-date submissions |

The Driver paper explicitly places the observations from the sixteenth through
twentieth centuries and describes generalized approximate ranges. It therefore
cannot establish the target state at `1444-11-11`. Its paper and repository
also disagree on CC BY-NC 2.5 versus CC BY 4.0. Both problems remain explicit.

The Schwartzberg plates cover `1390–1450` and `1250–1550`, but are neither
exact-date snapshots nor licensed vector linework; the host prohibits
reproduction without permission. D-PLACE supplies later focal points, AIATSIS
and Native Land disclaim exact boundaries, Euratlas is a restricted 1500
snapshot, SUNGEO begins in 1895, and WHG is a record-specific discovery layer
requiring reproducible per-record retrieval and licensing.

## Decision boundary

All 206 components and 180 pairs remain rejected. Exact source-feature binding
does not establish identity between a synthetic actor and a historical entity.
A later generalized polygon cannot establish target-date component ownership
or an exact shared line. No record qualifies for independent acceptance, so
there is no implementation, QA, tolerance, grade, permission, or Task 17
change.

## Verification

```bash
.venv/bin/pytest -q tests/test_m25c_exact_source_evidence.py
```

The test verifies every record hash, artifact hash, frozen ID surface, source
file checksum, and fail-closed decision.
