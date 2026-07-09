# History

## 2026-07-09 - M1 Source Adapter Implementation

- Implemented real Natural Earth and geoBoundaries source artifact downloads
  behind `gpm sources download --execute`, while preserving the default dry-run
  planning behavior.
- Added atomic raw artifact writes, local raw artifact inspection, SHA-256
  checksum capture, access dates, version/original-format metadata, and
  persisted downloaded/build source manifests.
- Extended source manifests with per-artifact records and added deterministic
  mocked-download tests for the downloader and CLI path.
- Next project task: generate the first modern global land province draft from
  downloaded source artifacts.

## 2026-07-09 - Phase 1 Scaffold Wrap-Up

- Added the Python project scaffold and `gpm` CLI command surface for source
  planning, future builds, exports, and QA.
- Added license-aware source policy config, generation profiles, JSON schemas,
  source adapter stubs, and tests for the Phase 1 contract.
- Added documentation that maps the scaffold to the roadmap and explains schema
  ownership.
- Hardened the package boundary so installed wheels can find bundled configs
  and schemas, and so unknown CLI profiles return clean errors.
- Next project task: implement M1 source adapter downloads and persisted source
  manifests without committing raw geodata.
