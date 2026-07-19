# M25B game runtime compiler and reference pack

M25B turns an accepted canonical historical status document into a deterministic,
engine-neutral game pack. It also accepts the synthetic M25A hard-case casebook
to build the committed conformance pack. This does not certify any historical era.

```bash
gpm export runtime \
  --canonical-input tests/fixtures/m25a/casebook.json \
  --output-dir exports/m25b-reference \
  --pack-id m25b-hard-cases-v1 \
  --compatibility-revision 1 \
  --benchmark
```

## Runtime contract

`runtime_manifest.json` is the root contract. It pins format version `1.0.0`,
the save-compatibility revision, deterministic counts, entrypoints, size metrics,
and the SHA-256 plus byte length of every distributed asset.

- `core/stable_ids.json` maps persistent IDs to deterministic pack-local dense
  indices. Saves and public APIs store stable IDs, never dense indices.
- `core/*.bin` contains fixed-width component, province, political-unit, and
  ordered province-membership tables. Province rows contain hierarchy indices.
- `graphs/{land,sea,strait,port}.csr` contains unsigned 32-bit CSR offsets and
  neighbors. Edges are symmetric and sorted.
- `scenarios/base.bin` is the base political state. Later scenarios are sorted,
  deterministic remove/add deltas, indexed by `scenarios/index.json`. Compact
  per-scenario union tables retain composite/dynastic political relationships.
- `geometry/lod0.tri` through `lod2.tri` are pre-triangulated display/picking
  meshes. `geometry/map.pmtiles` is a PMTiles v3 MVT archive. Runtime startup
  does not parse canonical GeoJSON.
- `migration.json` declares source/target compatibility revisions and explicit
  old-to-new province ID mappings. Unchanged stable IDs remain compatible.
- `debug/symbols.json` is emitted only with `--debug-symbols`. Normal packs
  exclude canonical evidence and raw location/source artifacts.

Binary files use little-endian integers/floats and an eight-byte format magic.
The reference implementation is `gpm.runtime.RuntimePack`; it verifies hashes,
resolves stable and dense IDs, reads CSR neighbors, applies scenario deltas, and
resolves saved province IDs. It performs no union, topology, georeferencing, or
historical-source operation.

## Reproducibility and performance

The compiler sorts every public identity and relationship, uses canonical JSON,
sets deterministic gzip timestamps in reused PMTiles/MVT infrastructure, and
omits wall-clock timestamps and build paths. Compiling into two clean directories
must yield byte-identical trees.

`RuntimePack.benchmark(path)` reports verified core-load latency and peak Python
allocation. The manifest records core, compressed-core, initial core plus LOD0,
and complete geometry sizes for the roadmap acceptance budgets. Viewport p95 is
an integration benchmark for a concrete storage/HTTP environment and is not
fabricated by the local compiler benchmark.

The committed `samples/m25b-runtime-reference/` pack is synthetic contract data,
not a historical release. Regenerate it with `scripts/build-m25b-reference.py`.
