# 1444 global v1

This is the M25C worldwide lineage for **1444-11-11**. Its permanent pass and
runtime identity is `official-1444-global-v1`; the eventual public scenario ID
is `official-1444`.

The checked-in worldwide pass lineage is intentionally **not accepted**. Its
anomaly census is now driven by the tracked `census-research.json`, which records the rejected
packet baseline, source metadata, anomaly and polity records, and one
class-specific review for every one of the 242 region/class cells. The
deterministic generator renders that input and the tracked
`source-access-audit.json` into an ignored, hash-locked packet; it does not
contain embedded regional aliases or review conclusions.

The canonical treatment of the reviewed cases is recorded in
`docs/m25c-anomaly-alignment-decisions.md`. The 242-cell matrix is a fixed set of
search classes, not a requirement to manufacture one positive case per class.
The current aligned baseline contains ten positive geographic anomaly records;
the historically supported Lancastrian claim is retained as a non-geographic
gazetteer relationship.

The generated inventory remains permanently unsigned. George Le approved the
242-cell census on 2026-08-14; acceptance is recorded only in the ignored local
`review_acceptance.json` sidecar, which binds
the reviewer, review date, pass identity, reviewed counts, and SHA-256 of the
frozen `SHA256SUMS`. Signing never rewrites or rehashes the research artifacts.
Worldwide historical evidence beyond this census, complete M23 fabric
assignment, gap-free grade-A regional coverage, assembled-pass review, runtime
certification, and release remain separate hard gates.

Generate and verify the frozen pending-review census with:

```sh
python scripts/generate-m25c-anomaly-census.py
python scripts/verify-m25c-anomaly-census.py verify --state pending
```

To recreate the recorded local approval after regenerating the frozen packet:

```sh
python scripts/verify-m25c-anomaly-census.py sign \
  --reviewer "George Le" --review-date 2026-08-14
python scripts/verify-m25c-anomaly-census.py verify --state accepted
```

Future research changes require editing `census-research.json`, regenerating a
new frozen packet, and obtaining a new acceptance binding. Never patch a frozen
packet.

The downstream research pipeline begins by consuming both frozen inventory and
its acceptance sidecar:

```sh
python scripts/build-m25c-global-pass.py inventory \
  --inventory-input data/processed/m25c-global-staging/evidence/anomaly_inventory.json \
  --acceptance-input data/processed/m25c-global-staging/evidence/review_acceptance.json
python scripts/build-m25c-global-pass.py fabric \
  --fabric-input <accepted-m23-r2/locations.geojson> \
  --fabric-sidecars-dir <accepted-m23-r2>
python scripts/build-m25c-global-pass.py evidence --evidence-dir <reviewed-schema-0.3-bundle>
python scripts/build-m25c-global-pass.py splits
python scripts/build-m25c-global-pass.py aggregation
python scripts/build-m25c-global-pass.py assembly
python scripts/build-m25c-global-pass.py render
gpm qa start-date --pass-dir research/start-dates/1444-global-v1 --pending-review
```

The combined `research-pipeline` stage validates the complete curator handoff
before writing any supplied artifact. It emits `m25c_rejection_report.json`,
grouped by artifact, rule, affected IDs, and remediation owner, and stops if
any inventory, accepted-fabric sidecar, schema identity, contained path, or
checksum requirement fails. The individual stages remain available for
diagnosis. The accepted M23 handoff must include its fabric manifest, lineage,
province membership, and location adjacency sidecars; the schema-0.3 evidence
bundle must carry and hash-pin the aggregation and release sidecars.

A promotable schema-0.3 anomaly inventory is a closed census, not merely a list
of examples. Its `census.region_ids` is the exact 22-subregion non-Antarctic UN
M49 partition, `census.types` contains all 11 anomaly classes, and
`census.cells` contains each of the 242 region/class pairs exactly once. The
required `anomaly_census_review_ledger.json` mirrors that matrix and records
region-specific survey locators, class-specific queries, considered leads and
dispositions, supporting source IDs, rationale, and a dated conclusion.

Validation rejects missing ledger cells, unknown or unreviewed sources,
inventory/ledger mismatches, survey evidence outside 1444-11-11, survey
dependence on the common atlas, reused generic URL/locator aliases, generic or
temporally unbounded queries, templated negative rationales, incomplete failure
bases, rejection-log drift, incomplete live-URL coverage, and positive cases
without two independent provenance groups. Every supporting source requires an
exact ledger locator, and every anomaly subject must resolve to a sourced
gazetteer polity. The downstream
inventory stage also requires a valid acceptance sidecar and overlays the
reviewer/date in memory before materializing its canonical reviewed inventory.

`fabric` assigns exact UN M49 subregion codes from Natural Earth metadata and
excludes Antarctica from the playable world mask. `splits` preserves revision
2 by default; revision 3 additionally requires a failed paintability report,
reviewed split requests, and complete parent/child lineage. `aggregation`
requires exactly 22,000 provinces, exact-once world-mask assignment, no modern
boundary influence, and merge-blocking historical hard constraints.

The later assembled-pass review remains unchanged and is a separate gate:

```sh
python scripts/build-m25c-global-pass.py accept-review \
  --reviewer "<human identity>" --review-date YYYY-MM-DD
```

That command reviews the assembled pass and its render sheets; it is not a
substitute for packet-specific census signing. Runtime compilation,
certification, and demo promotion remain outside this research boundary.
