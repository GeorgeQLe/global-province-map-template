# M25C remaining Grade C implementation ship manifest

Date: `2026-08-24`
Status: **all eight remaining accepted routes implemented; candidate remains blocked**

## User goal

Serially implement the eight remaining independently accepted Grade C routes
in regions `017`, `018`, and `053`, preserve every reviewed hash and explicit
gap, regenerate affected and worldwide QA, and keep every release permission
closed.

## Changed files and purpose

- `scripts/generate-m25c-provisional-pass.py` — binds and applies all eleven
  accepted routes in reviewed order, including the eight remaining routes.
- `src/gpm/qa/m25c_assembled.py` — defines the exact four allowed Grade C
  geometry rows, their region-specific gaps, and the eleven-change serial
  changelog suffix.
- `tests/test_m25c_global_certification.py` — verifies all route hashes,
  component closure, gaps, changes, and fail-closed review drift.
- `tests/test_m25c_assembled_transition.py` — updates the valid assembled
  fixture and preserves rejection of extra or altered coverage exceptions.
- `README.md`, the best-reasonable evidence docs, and task state files — record
  full implementation, unchanged QA totals, and residual blockers.
- `tasks/m25c-remaining-grade-c-implementation-ship-manifest.md` — records this
  shipping boundary and verification evidence.

## User-goal mapping

The generator applies precisely the requested eight routes after the existing
region `014` suffix. The shared qualifier constrains the resulting three new
Grade C rows and all eleven ordered changes. The tests prove exact hash,
component, gap, exception, and order behavior. The regenerated render and
ordinary preflight prove the affected output and unchanged fail-closed release
state. The documentation reports completion without claiming Grade A,
certification, or publication.

## Serial implementation boundary

The already implemented region `014` changes remain first. The generator then
applies these exact routes in order:

1. `017/NON_EXECUTABLE_SEAM_ASSERTION` — decision
   `36dfd24589d7369d831a39e4302bc4c2e6259781f8ebd1a1da2ae498f0c96985`;
   evidence `798b15236b8c194f5c2976fe342b83ef5d588d95e7066f59f75d601cac00bebc`.
2. `017/SPATIAL_ASSERTION_FAILED` — decision
   `61abdaea1901610878ddb31af364a0f947f4f19b5043fd0cf05d47d27b6eb656`;
   evidence `8f8de8052b0bdac35d7fdbc856c92d35ae2e1ec8163d5cfe3c8d805801f778bb`.
3. `017/UNCERTIFIED_A_GRADE` — decision
   `41e678055d9e1fe2619846e7ea9e870ecf6dbd8df0abce0a50427796cfe05236`;
   evidence `6318ff533a18a4a0004d876af49a3de88d2f303b53017fdc97f5f87e7c6048d1`.
4. `018/NON_EXECUTABLE_SEAM_ASSERTION` — decision
   `64248689278c0bb0062a1cc958a5b9a3a560ef4340ee54349370aebe3de56f4d`;
   evidence `2c2f99ac33dcdc1ddffc1b3cb20e35375eb2c00cb94eeeec52b04558a91efc8c`.
5. `018/SPATIAL_ASSERTION_FAILED` — decision
   `87d85e9074c672bc13b28a733fdc817cc98fab6e2dbf1c4c2ee45995b932c986`;
   evidence `16aeac35e6ccb97593d1a067d2752dc65935a53202a10264fd3e3aa5233c86a3`.
6. `018/UNCERTIFIED_A_GRADE` — decision
   `8c36312d47e1ef5ef4cd96988c3ab2940d232f8625e4d5407a80ae1cb224cd21`;
   evidence `6ec02ff944591ea1ba90ad4509a187bf677933fe072f71f8f395c3be2055c490`.
7. `053/SPATIAL_ASSERTION_FAILED` — decision
   `850028ea78fe16d2c5c8c9c8bf3d32e3aed29a775900294df2f667ef70b83043`;
   evidence `b97c8808de3dfcfa23756d481cc7bf81041b1cc44f3ed5c47c50a092d19e2446`.
8. `053/UNCERTIFIED_A_GRADE` — decision
   `321f2c61ec736b6e0a3375c762ac48dd6c112c9763113a6c3fd8f6e63334ba57`;
   evidence `c861d01f2a8ee0b01a4ec933ee7cf7029f2c8de6df2b0fbf21f211460b3f4e4c`.

Generation pins review-sidecar SHA-256
`d16873c6ea3a10ca8127ddef04099c101cc8c7322e81c023ca4c56e9dc6acebd`,
rechecks every reviewed artifact, and requires exact accepted component closure:
36 components for `017`, 32 for `018`, and 18 for `053`.

## Honest Grade C result

Only the three requested geometry coverage rows change. Each records the
1400/1492 bracket, representative-point-only testing, absent source-derived
edges/error/full-containment proof, and the exclusion of political actors,
facets, relationships, and Grade A/B. Regions `017` and `018` also retain their
non-executable and failed negative seams. Region `053` retains its executed,
failed Western Australia-South Australia seam. No geometry, component, actor,
relationship, assertion tolerance, packet, or permission changes.

## Tests run

- Executable focused implementation/review/assembly suite: `77 passed in
  2.20s`; no warnings.
- Executable full configured suite: `437 passed in 67.34s`; no warnings.
- Executable assembled candidate regeneration and qualification: completed.
- Executable review render: all `30` sheets regenerated.
- Executable ordinary worldwide preflight: expected fail with `56` non-review errors and
  `1` pending-review warning. Counts are four applicability, four global Grade
  C coverage, 18 missing positive-border, eight non-executable seam, 13
  spatial, nine uncertified Grade-A, and one invalid-review warning.
- Candidate status remains `assembled_pending_research_qa`; review acceptance,
  certification, runtime publication, and public release remain false.
- Patch hygiene: `git diff --check` passed.
- Documentation-only checks: todo, roadmap, history, packet status, and the
  exact generated coverage/changelog were reconciled against the diff.

## Skipped tests

No separate lint, typecheck, or build command is configured in
`pyproject.toml`, and the repository has no root `CLAUDE.md`, Makefile,
Justfile, package scripts, `setup.cfg`, or `Cargo.toml` supplying one. The full
configured pytest suite, Python import/compilation exercised by that suite,
assembled qualification, render, and ordinary preflight are the applicable
project gates. No conversation export was requested. Deploy is skipped because
the repository has no `deploy.md` or `tasks/deploy.md` manual deploy contract.

## Adversarial review

The equivalent targeted audit challenged review-sidecar drift, reviewed-input
drift, decision and evidence hash mismatch, incomplete or extra component
closure, missing or altered Grade C gaps, extra coverage exceptions, and a
missing or reordered serial changelog suffix. The implementation or tests fail
closed at every boundary. The audit also inspected the generated candidate:
only `014`, `017`, `018`, and `053` geometry are Grade C, with gap counts
`6/6/6/5`, and its last eleven changes match the reviewed route order exactly.

## Residual risk and rollback

All Grade C geometry remains approximate and incomplete. All rejected routes,
180 pair dispositions, and 206 component decisions remain fail-closed and need
stronger evidence. Task 17 remains blocked until geometry is gap-free Grade A
and ordinary QA has zero errors. Revert this change as one unit to restore the
three affected Grade-A packet claims; no runtime or public migration occurred.

## Next command

`$exec` — obtain stronger, actor/component-specific evidence for the remaining
rejected records and ordinary-QA blockers before Task 17 review can open.
