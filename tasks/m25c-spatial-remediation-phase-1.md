# M25C spatial-remediation phase 1 implementation

Status: **implemented; remaining evidence gates fail closed**
Start date: `1444-11-11`
Implementation date: `2026-08-23`

## Outcome

This phase implements only the five decisions approved in task 15. It does not
relax a tolerance, infer a hard historical frontier, approve an independent
review, or enable any review, certification, runtime, publication, or
deployment permission.

- Seam observability now requires complete usable-seam coverage by valid,
  fully non-unknown components whose evidence is reviewed and date-valid.
  Deterministic seam-normal samples must resolve on both sides inside the fixed
  `75 km` corridor. A covered seam with no compositional transition is an
  executable `0.0`; missing, partial, ambiguous, invalid, or unknown coverage
  remains null and fails closed.
- Southern Europe reconstructs exactly nine coarse components intersecting the
  approved Italy-Slovenia corridor. Each has the same explicitly shared and
  contested Venetian-Habsburg-Hungarian frontier fabric. The other 455 region
  records remain unknown, and no modern-country dispatch is used.
- The five border-applicability candidates (`021`, `053`, `054`, `057`, and
  `061`) are revision-, component-inventory-, source-hash-, and hard-anchor-
  bound. Their independent reviews remain pending, and incomplete adjacency
  audits fail dedicated QA without suppressing any missing-border finding.
- An official CAOP Portugal-Spain segment was independently extracted and
  provenance-pinned as a research candidate. It is not promoted: the nearest
  current two-sided subject edge exceeds the declared error budget, independent
  hash review is pending, and segment-specific 1444 corroboration is incomplete.
- The Raichur review found no second source independent of the Kadiri
  inscription tradition that supplies exact two-sided geometry. No point,
  zone, or hard line was promoted.

## Exact Southern Europe record set

The pre-change eligible affected-component set for the non-executable `039`
seam was empty. Phase 1 changes only these province/component records:

- `prv_09be1f2b49e888579cb7`
- `prv_124f2c3c7427e9b49fc8`
- `prv_134894c766f1b126146b`
- `prv_1b8a54b0c098d8c2cf09`
- `prv_23535148c54f1b807d57`
- `prv_24db15d5ae130c8a28f3`
- `prv_4135770ab968f38bca67`
- `prv_7ee3d24c2bcf29c026f3`
- `prv_f45f86dd0797a2cb63f4`

Each record changes from five unknown facets and no status relationship to
`habitable`, `resident`, `mixed`, `contested`, and `shared`, with
`territorial_presence` relationships for `scenario-hab`, `scenario-hun`, and
`scenario-ven`. It asserts a coarse shared frontier fabric, not an exact line.

## Regeneration and ordinary QA

Two complete assembled trees were generated independently under
`/private/tmp/m25c-spatial-phase1-run1` and
`/private/tmp/m25c-spatial-phase1-run2`; `diff -qr` found no difference. The
first tree rendered 30 review sheets. Ordinary pending-review QA reports 58
non-review errors and one expected independent-review warning:

| Finding | Count |
| --- | ---: |
| `BORDER_APPLICABILITY_NOT_QUALIFIED` | 5 |
| `MISSING_POSITIVE_BORDER_ASSERTION` | 19 |
| `NON_EXECUTABLE_SEAM_ASSERTION` | 8 |
| `SPATIAL_ASSERTION_FAILED` | 13 |
| `UNCERTIFIED_A_GRADE` | 13 |
| `INVALID_INDEPENDENT_REVIEW` (warning) | 1 |

The covered-zero contract makes `039`, `057`, and `061` executable `0.0`
passes. Regions `029` and `054` remain executable `0.0` passes, and `021`
remains below tolerance at `0.185554`. The stricter completeness rule exposes
eight partial-coverage seams as non-executable instead of treating a partial
measurement as sufficient evidence. All candidate permissions remain false.

## Remaining gates

Task 16 remains the next decision boundary. Each unresolved corridor or border
must receive a separately reviewed evidence packet. The five applicability
records require complete land-adjacency dispositions and independent review of
their bound hashes. Portugal-Castile additionally requires fabric refinement
or another independently derived two-sided binding within the declared error
budget. Raichur requires genuinely independent spatial corroboration.
