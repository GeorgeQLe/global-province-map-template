# M25C assembled-pass transition research

Status: **approved and implemented; assembled candidate remains QA-blocked**
Start date: `1444-11-11`
Research date: `2026-08-21`

## Scope and result

The regional evidence replacement needed for an assembled worldwide pass is
complete: the tracked packet directory contains exactly one qualified packet
for each of the 22 non-Antarctic M49 subregions, exactly 22,000 assignment
overrides, and exactly 88 gap-free Grade-A coverage rows. The generated final
evidence artifacts contain no reference to
`official-1444-modern-scaffold-provisional`.

That does **not** make the present output promotable. The generator still emits
`qa_mode: provisional_internal_review`, an aggregation manifest with
`provisional: true`, and canonical status with `provisional: true` on all 22,000
components and all 22,000 provinces. Its dossier, changelog, version, report
name, candidate status, and CLI contract also describe provisional output.
Changing only the manifest mode would create contradictory lineage.

Full-strength research QA is also intentionally not clean. A fresh current
assembly has 35 hard findings even in provisional mode: 16 failed modern-seam
assertions, 16 resulting `UNCERTIFIED_A_GRADE` geometry rows, and three
`NON_EXECUTABLE_SEAM_ASSERTION` findings. Provisional mode additionally
downgrades 19 missing positive-border assertions and the pending review gates.
After a complete render bundle removes the two incomplete-render findings, an
assembled pass under ordinary pending-review QA would therefore retain exactly
54 non-review errors: the existing 35 plus 19 missing positive borders. The
pending human signature is the sole review warning that preflight may waive.

The recommendation is a two-gate state transition, not a direct promotion:

1. an explicit, fail-closed **assembled-pass qualification** may remove
   provisional lineage labels only after final-artifact and input-acceptance
   checks succeed; then
2. ordinary pending-review QA must pass with zero non-review errors before the
   candidate can become eligible for independent human acceptance.

The current bytes satisfy much of gate 1, but they fail gate 2 and must remain
non-accepting, non-certifiable, non-publishable, and non-runtime-promotable.

## Current transition hazards

### A mode-bit flip is insufficient

`run_start_date_qa` selects its downgrade policy from the pass manifest. Merely
removing `qa_mode` or changing it to `certification_review` activates ordinary
QA, but does not prove that the underlying artifacts stopped being provisional.
The canonical and aggregation flags would still say otherwise, and the version,
dossier, and changelog would still claim a provisional seed.

The canonical schema currently permits extra `provisional` properties and QA
does not independently reject them in certification mode. Consequently the
transition qualifier must inspect the final artifact graph, and ordinary QA
should gain a certification-review check that rejects any surviving
provisional marker or source identifier.

### The generic assembly stage can relabel unqualified bytes

`scripts/build-m25c-global-pass.py assembly` checks that the expected artifact
files exist and then writes a manifest without `provisional_internal_review`.
It does not prove exact regional-packet closure, anomaly-census acceptance,
absence of provisional sentinels, or absence of provisional canonical flags.
It can therefore rewrap output from the provisional generator even though the
later QA and acceptance gates still reject the current research defects.

The assembly stage must call the same final-artifact qualifier as the generator
or refuse generator-produced output. There should be one authoritative
transition function, not two ways to change lineage state.

### Candidate status is descriptive, not an authority

`candidate_status.json` is not part of the pass manifest's hashed artifact
table and is not consumed by certification. It is useful operator state, but it
cannot be the promotion gate. Authority remains the hashed pass manifest,
ordinary QA report, exact render manifest, human review binding, runtime pack,
and final certification bundle.

## Recommended state machine

| State | Manifest / candidate state | Allowed next action |
| --- | --- | --- |
| Provisional generation | `provisional_internal_review`; all four candidate permissions false | Internal diagnostics only |
| Assembled, QA-blocked | `certification_review`; `assembled_pending_research_qa`; all four permissions false | Ordinary QA and remediation |
| Assembled, review-ready | `certification_review`; `pending_independent_review`; only `review_acceptance_allowed` true | Independent human review |
| Accepted research pass | accepted review binding; public, certification, and runtime-publication permissions still false | Runtime compile and certification |
| Certified bundle | separate accepted global-certification manifest | Demo/publication tooling may consume the pinned bundle |

No state may be inferred from a filename, directory name, candidate-status
claim, or the presence of 22 packets alone. Each transition recomputes its gate
from pinned bytes.

## Exact assembled-pass qualifier

Add an explicit mode such as `--assembly-mode assembled-pass`; retain the
current provisional mode as the default. Build into a staging directory and do
not emit a certification-review manifest if any qualifier below fails.

The shared qualifier should require all of the following:

1. **Accepted inputs.** Verify the anomaly census against its immutable
   acceptance sidecar, and verify the accepted M23 fabric manifest, lineage,
   membership, adjacency, contained paths, and checksums. Reuse the existing
   handoff validators rather than trusting a populated staging directory.
2. **Exact regional closure.** Require exactly 22 packets, exactly one packet
   for each pinned M49 subregion, no duplicate or superseding packet ambiguity,
   all existing Grade-A packet qualifications, exactly 22,000 final assignment
   overrides, and exact-once coverage of the 23,582-location world mask.
3. **Exact final coverage.** Require exactly the 88 `(region, layer)` pairs,
   every row Grade A with no exclusions or known gaps, and no top-level coverage
   exclusions or gaps. This proves assembly completeness only; ordinary QA
   still decides whether those grades are earned by passing assertions.
4. **No provisional evidence lineage.** Reject the provisional source ID or
   other approved legacy sentinel anywhere in source, gazetteer, boundary,
   assertion, assignment, coverage, canonical-status, dossier, or changelog
   evidence claims. Require every cited final source to resolve and be reviewed.
5. **Truthful artifact metadata.** Emit a distinct assembled artifact version
   and changelog entry; set the aggregation result non-provisional; omit or set
   false the canonical component/province provisional flags; set canonical and
   pass `qa_mode` consistently to `certification_review`; and replace the
   provisional dossier/migration language. Reject mixed modes.
6. **Byte and path integrity.** Recompute all artifact and sidecar hashes only
   after the final metadata rewrite, reject symlinks and contained-path escapes,
   and make the output transition transactional so a failed qualifier cannot
   leave a partially relabeled directory.

The qualifier must not require spatial assertions to pass. Keeping assembly
completeness separate from research correctness lets ordinary QA report the
real defects without disguising the candidate as provisional. It also must not
set `review_acceptance_allowed` merely because qualification succeeds.

## Ordinary-QA and review gate

After assembled qualification, run deterministic generation twice and compare
the complete artifact trees, render the 22 regional sheets plus every represented
anomaly-class sheet, and run `gpm qa start-date --pending-review` in ordinary
mode. Only a zero-error result may change candidate status to
`pending_independent_review` and enable `accept-review`.

`accept-review` should retain its existing transactional behavior: verify the
complete pinned render set, write the proposed human binding, rerun ordinary QA,
and restore the previous manifest and review bytes on failure. Certification
must continue to rerun ordinary QA and enforce canonical/runtime parity,
determinism, performance, accepted review, bundle containment, and hashes.
Demo and site publication must continue to require the accepted certification
bundle.

The generic `assembly` stage should either invoke this qualifier or be narrowed
to artifacts produced by the accepted-input pipeline. A test must prove it
cannot remove the provisional guard from an otherwise valid provisional pass.

## Current QA impact

If the current complete packet set is emitted in assembled-pass mode and fully
rendered, expected pending-review QA is:

- 16 `SPATIAL_ASSERTION_FAILED` errors in regions `005`, `011`, `013`, `014`,
  `015`, `017`, `018`, `030`, `034`, `035`, `039`, `053`, `057`, `061`, `143`,
  and `145`;
- 16 corresponding `UNCERTIFIED_A_GRADE` geometry errors;
- three `NON_EXECUTABLE_SEAM_ASSERTION` errors in `039`, `057`, and `061`;
- 19 `MISSING_POSITIVE_BORDER_ASSERTION` errors in every region except `151`,
  `154`, and `155`; and
- one pending independent-review warning, which is the only warning the
  pending-review preflight may tolerate.

That is 54 non-review errors, so no review-ready state should be emitted. The
transition exposes these defects at their real severity; it does not resolve
them. The existing task sequence must add decision-gated research/remediation
for the 16 seam failures, the three non-executable regions, and the 19 positive
geometry requirements before a final human review bundle can be presented for
acceptance.

## Alternatives and tradeoffs

1. **Recommended: explicit assembled qualification followed by ordinary QA.**
   This records that evidence replacement is complete while preserving every
   correctness and release gate. It requires shared qualification code and a
   small explicit state machine.
2. **Change only `qa_mode`.** This is mechanically small but leaves 44,000
   canonical provisional flags, a provisional aggregation flag, and provisional
   narrative/version metadata. Rejected as contradictory and forgeable.
3. **Keep provisional mode until every spatial defect is fixed.** This is safe,
   but it continues downgrading the 19 missing-border findings and obscures the
   distinction between completed packet replacement and failed ordinary QA.
4. **Let ordinary QA alone detect provisional residue.** Current QA does not
   reject every metadata marker, accepted-input binding is upstream of QA, and
   a generic assembly stage can rewrite the manifest first. Rejected unless
   paired with the explicit qualifier.
5. **Permit human review of the current failing bundle.** Render inspection is
   useful during remediation, but an acceptance-capable final review bundle
   must not be issued while 54 non-review errors remain. Rejected.

## Required regression contracts

Implementation should add focused tests for default-provisional behavior;
explicit opt-in; missing, duplicate, or extra regional packets; incomplete or
overlapping assignment overrides; unaccepted anomaly input; changed fabric
sidecars; provisional sentinel leakage in every final artifact class; mixed
canonical/manifest modes; exact 88-row closure; transactional failure; and the
generic assembly-stage relabeling path.

The existing tests that reject provisional `accept-review`, certification, and
demo promotion must remain. Add a current-world fixture proving that assembled
qualification succeeds but pending-review preflight fails with the expected 54
non-review errors and does not enable review acceptance. Add a synthetic clean
fixture proving that only zero-error preflight reaches review-ready state.

## Reviewer decision requested

Approve or amend the following bundle before implementation:

1. add a default-safe explicit assembled-pass mode and one shared final-artifact
   qualifier used by every assembly entry point;
2. require accepted anomaly/fabric bindings, exact 22-packet and 22,000-override
   closure, exact 88-row coverage, reviewed-source closure, no provisional
   residue, truthful metadata, containment, hashes, and transactional output;
3. treat assembled qualification as `assembled_pending_research_qa`, with all
   review, certification, runtime-publication, and public-release permissions
   still false;
4. enable independent review acceptance only after a complete render and
   zero-error ordinary pending-review QA; and
5. keep the current candidate blocked on the exact 54 non-review errors, then
   add separate decision-gated research/remediation before final human review.

The five-part recommendation was implemented on 2026-08-22. The assembled
candidate reproduces the predicted 54 non-review errors plus the sole expected
pending-review warning. No research defect was remediated and no review,
certification, runtime, publication, or deployment permission was enabled.
