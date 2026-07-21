# 1444 global v1

This is the M25C worldwide lineage for **1444-11-11**. Its permanent pass and
runtime identity is `official-1444-global-v1`; the eventual public scenario ID
is `official-1444`.

The checked-in candidate is intentionally **not accepted**. It is the preserved
pre-research seed: its placeholder anomaly rows document missing curator input
and are not accepted by the M25C builder or QA. Worldwide historical evidence,
complete M23 fabric assignment, gap-free grade-A regional coverage, and
independent review remain hard gates. The builder never manufactures or waives
those inputs, and this research task deliberately stops before runtime or
global certification.

The deterministic research pipeline is:

```sh
python scripts/build-m25c-global-pass.py inventory --inventory-input <reviewed-anomalies.json>
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
`census.cells` contains each of the 242 region/class pairs exactly once. Every
cell is either `resolved_cases`, with matching anomaly links, or
`reviewed_none_found`, with reviewed survey-source links and an explanatory
note. The named researcher and human reviewer must differ. Every anomaly and
census source must resolve to a reviewed schema-0.3 source-manifest record, and
every anomaly subject must resolve to a sourced gazetteer polity. The combined
handoff canonical-compares an inventory duplicated in the evidence bundle with
`--inventory-input`; disagreement is rejected before copying.

`fabric` assigns exact UN M49 subregion codes from Natural Earth metadata and
excludes Antarctica from the playable world mask. `splits` preserves revision
2 by default; revision 3 additionally requires a failed paintability report,
reviewed split requests, and complete parent/child lineage. `aggregation`
requires exactly 22,000 provinces, exact-once world-mask assignment, no modern
boundary influence, and merge-blocking historical hard constraints.

After inspecting all 22 regional sheets and every anomaly-class sheet, an
independent human records acceptance explicitly:

```sh
python scripts/build-m25c-global-pass.py accept-review \
  --reviewer "<human identity>" --review-date YYYY-MM-DD
```

The command rejects generator identities, missing sheets, and changed render
hashes; repins the accepted review; runs ordinary fail-closed start-date QA;
and keeps `public_release_allowed: false`. Runtime compilation, certification,
and demo promotion belong to the subsequent M25C task.
