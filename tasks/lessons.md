# Lessons

## 2026-08-24 — Preserve the distinction between exact and best-reasonable evidence

- When an exact global source search cannot qualify every deferred finding and
  the user asks for the best reasonable attempt, produce a complete,
  confidence-graded evidence surface instead of treating exact-source failure
  as the end of the research task.
- Keep the qualification boundary explicit: bracketing or incompletely sourced
  geometry may support a zone or documented Grade-B/C reconstruction, but it
  does not become surveyed Grade-A linework through aggregation.
- Correction enforcement: the M25C generator and executable tests now require
  exact 43-finding, 180-pair, and 512-component coverage, record-level hashes,
  pinned input hashes, confidence labels, and pending independent review.

## 2026-08-14 — Do not reopen locked review decisions

- When a task explicitly says prior treatments are locked and confirmed
  negatives proceed silently, do not describe those decisions as awaiting a
  second substantive human review unless contradictory evidence is found.
- Distinguish evidence review from the administrative act of recording a
  signature. If the user already made the decisions and the audit finds no
  exceptions, report that no further review is required and ask only for the
  identity/date needed by the acceptance sidecar.
- Correction enforcement: the active M25C todo and roadmap now treat the census
  review as complete and route next work to worldwide pass assembly; the packet
  verifier continues to enforce the separate cryptographic signature boundary.
