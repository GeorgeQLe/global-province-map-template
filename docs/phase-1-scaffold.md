# Phase 1 Scaffold

This repository now contains the Phase 1 foundation described in `ROADMAP.md`.
It is intentionally a code and contract scaffold only: no raw geodata is
downloaded, generated, or committed.

## Roadmap Mapping

- `pyproject.toml` defines the Python project and the `gpm` CLI entrypoint.
- `src/gpm/` contains the command-line stubs, config loaders, source manifest
  helper, schema loader, and the future source adapter package.
- `configs/profiles/` contains the initial generation profiles from Phase 9:
  `modern-small`, `modern-detailed`, `hoi-like`, `victoria-like`, and `eu-like`.
- `configs/sources.toml` records the Phase 0 data policy in machine-readable
  form.
- `schemas/` contains JSON Schema contracts for source manifests, attribution
  records, province entities, region entities, and adjacency records.
- `tests/` checks that profiles parse, default source policy stays permissive,
  restricted sources are excluded, and the stub CLI runs.
- `data/raw/`, `data/intermediate/`, and `data/processed/` are ignored by git
  and reserved for local future runs.

## Source Policy

The default profile path includes only Natural Earth and geoBoundaries. GHSL and
WorldPop are listed as deferred default candidates because citation and raster
adapter behavior still need to be implemented. OpenHistoricalMap is optional.

OpenStreetMap is marked optional and isolated because ODbL-derived databases
must not be mixed into the permissive default build path. GADM is marked
restricted and excluded from default builds unless permission is obtained.

## M1 Source Adapters

M1 implements the adapters named in `configs/sources.toml`:

- `gpm.sources.adapters.natural_earth`
- `gpm.sources.adapters.geoboundaries`

`gpm sources download` still defaults to a dry run. Use
`gpm sources download --execute` to fetch raw artifacts into ignored local
storage under `data/raw/`, calculate SHA-256 checksums, and write
`source_manifest.json`. Use `gpm sources manifest --from-raw` to rebuild a
downloaded/build manifest from files that already exist locally.

Source manifests now include source-level metadata plus per-artifact URL, path,
access date, version, original format, byte count, and checksum. Downloaded raw
datasets remain outside git through the repository ignore rules.
