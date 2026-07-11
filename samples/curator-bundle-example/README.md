# Example curator bundle (M17)

Self-contained **external scenario bundle** for community / third-party
politics overlays. Official eras still live under `configs/scenarios/`; this
layout is for contributions that ship as a directory with a manifest.

## Layout

```
curator-bundle-example/
  bundle_manifest.json    # required
  README.md
  scenarios/*.json        # scenario definitions
  golden/*.json           # optional golden floors / borders
```

## Commands

```bash
uv run gpm curation list
uv run gpm curation validate --bundle curator-bundle-example
uv run gpm curation checklist --bundle samples/curator-bundle-example
uv run gpm curation import \
  --bundle samples/curator-bundle-example \
  --output-dir /tmp/imported-bundle

# Diff two scenarios (or ownership tables)
uv run gpm curation diff \
  --base-scenario modern-baseline \
  --target-scenario-path samples/curator-bundle-example/scenarios/community-demo-1444.json \
  --province-input samples/beta-license-audited/sample/provinces.geojson \
  --report-output /tmp/diff.json
```

## Contribution checklist

See [docs/m17-curation.md](../../docs/m17-curation.md) for the PR checklist,
golden-border schema, and deprecation policy when scaffold IDs change.
