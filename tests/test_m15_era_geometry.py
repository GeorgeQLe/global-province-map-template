"""M15: era-aware geometry packs, lineage maps, and priority-region apply."""

from __future__ import annotations

import json
from pathlib import Path

from gpm.cli import main
from gpm.era_geometry import (
    apply_era_geometry_pack,
    list_era_geometry_packs,
    load_era_geometry_pack,
    validate_era_geometry_pack,
)
from gpm.paths import ERA_GEOMETRY_DIR, PROJECT_ROOT
from gpm.release.quality import (
    QUALITY_TIER_PERIOD_GEOMETRY,
    accuracy_label,
)
from gpm.schemas import (
    SchemaValidationError,
    validate_era_geometry_lineage,
    validate_era_geometry_pack as schema_validate_pack,
)


def _land(province_id, *, country="FRA", region="FR-01", name=None, coords=None):
    ring = coords or [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [ring]},
        "properties": {
            "province_id": province_id,
            "display_name": name or province_id,
            "kind": "land",
            "parent_region_id": region,
            "parent_country_id": country,
            "area_sq_km": 100.0,
            "estimated_population": 1000.0,
            "terrain_class": None,
            "coastal": False,
            "island": False,
            "source_lineage": ["test"],
            "license_lineage": ["public domain"],
        },
    }


def _write_provinces(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": features},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_bundled_we_1444_pack_validates():
    packs = list_era_geometry_packs()
    by_id = {p.pack_id: p for p in packs}
    assert "we-1444-v1" in by_id
    summary = by_id["we-1444-v1"]
    assert summary.era == "1444"
    assert summary.scenario_id == "official-1444"
    assert summary.quality_tier == "period-geometry"
    assert summary.priority_region_id == "western-europe"
    assert "boundary_hints" in summary.geometry_modes
    assert "hard_overrides" in summary.geometry_modes
    assert summary.boundary_hint_count >= 4
    assert summary.hard_override_count >= 3

    document = load_era_geometry_pack("we-1444-v1")
    validate_era_geometry_pack(document)
    schema_validate_pack(document)
    assert (ERA_GEOMETRY_DIR / "we-1444-v1.json").is_file()


def test_apply_split_replace_and_lineage(tmp_path: Path):
    provinces = tmp_path / "provinces.geojson"
    _write_provinces(
        provinces,
        [
            _land(
                "sample_de_rhineland",
                country="DEU",
                region="DE-NW",
                name="Rhineland",
                coords=[[6.5, 50.5], [7.5, 50.5], [7.5, 51.5], [6.5, 51.5], [6.5, 50.5]],
            ),
            _land(
                "sample_be_flanders",
                country="BEL",
                region="BE-VLG",
                name="Flanders",
                coords=[[3.0, 50.5], [4.2, 50.5], [4.2, 51.2], [3.0, 51.2], [3.0, 50.5]],
            ),
            _land(
                "sample_fr_paris",
                country="FRA",
                region="FR-IDF",
                name="Paris",
                coords=[[2.0, 48.5], [2.8, 48.5], [2.8, 49.2], [2.0, 49.2], [2.0, 48.5]],
            ),
            _land(
                "outside_priority",
                country="ESP",
                region="ES-M",
                name="Madrid",
                coords=[[-4, 40], [-3, 40], [-3, 41], [-4, 41], [-4, 40]],
            ),
        ],
    )
    out = tmp_path / "era_out"
    result = apply_era_geometry_pack(
        "we-1444-v1",
        province_input=provinces,
        output_dir=out,
    )
    assert result.province_count_in == 4
    # Rhineland split 1→2; Flanders replaced; Paris identity; Spain identity
    assert result.province_count_out == 5
    assert result.hard_override_applied >= 3
    assert result.boundary_hint_count >= 4
    assert result.lineage_row_count == 5

    era_fc = json.loads((out / "provinces.geojson").read_text(encoding="utf-8"))
    ids = {f["properties"]["province_id"] for f in era_fc["features"]}
    assert "era_de_cologne" in ids
    assert "era_de_rhineland_residual" in ids
    assert "era_be_flanders" in ids
    assert "sample_fr_paris" in ids
    assert "outside_priority" in ids
    assert "sample_de_rhineland" not in ids

    cologne = next(
        f for f in era_fc["features"] if f["properties"]["province_id"] == "era_de_cologne"
    )
    assert cologne["properties"]["scaffold_province_id"] == "sample_de_rhineland"
    assert cologne["properties"]["era_geometry_mode"] == "hard_overrides"
    assert cologne["properties"]["era_priority_region"] is True

    spain = next(
        f for f in era_fc["features"] if f["properties"]["province_id"] == "outside_priority"
    )
    assert spain["properties"]["era_geometry_mode"] == "scaffold"
    assert spain["properties"]["era_priority_region"] is False

    lineage = json.loads((out / "lineage.json").read_text(encoding="utf-8"))
    validate_era_geometry_lineage(lineage)
    assert lineage["pack_id"] == "we-1444-v1"
    ops = {row["era_province_id"]: row["operation"] for row in lineage["rows"]}
    assert ops["era_de_cologne"] == "split_child"
    assert ops["era_be_flanders"] == "replace"
    assert ops["outside_priority"] == "identity"

    hints = json.loads((out / "boundary_hints.geojson").read_text(encoding="utf-8"))
    assert len(hints["features"]) == result.boundary_hint_count
    assert hints["gpm"]["layer"] == "boundary_hints"

    scope = json.loads((out / "quality_scope.json").read_text(encoding="utf-8"))
    assert scope["quality_tier"] == "period-geometry"
    assert "western-europe" in scope["period_true_scope"]

    assert (out / "lineage.csv").is_file()
    assert (out / "era_geometry_manifest.json").is_file()


def test_hard_overrides_skip_missing_scaffold_ids(tmp_path: Path):
    """Full NE builds without sample_* ids still get soft hints + identity lineage."""
    provinces = tmp_path / "provinces.geojson"
    _write_provinces(
        provinces,
        [
            _land("ne_fra_idf", country="FRA", region="FR-IDF"),
            _land("ne_deu_nw", country="DEU", region="DE-NW"),
        ],
    )
    out = tmp_path / "era_out"
    result = apply_era_geometry_pack(
        "we-1444-v1",
        province_input=provinces,
        output_dir=out,
    )
    assert result.province_count_out == 2
    assert result.hard_override_applied == 0
    assert result.hard_override_skipped >= 1
    assert result.boundary_hint_count >= 4
    era_fc = json.loads((out / "provinces.geojson").read_text(encoding="utf-8"))
    assert {f["properties"]["province_id"] for f in era_fc["features"]} == {
        "ne_fra_idf",
        "ne_deu_nw",
    }


def test_pack_validation_rejects_empty_modes():
    bad = {
        "schema_version": "0.1.0",
        "pack_id": "bad",
        "era": "1444",
        "display_name": "Bad pack",
        "quality_tier": "period-geometry",
        "priority_region": {"id": "x", "label": "X"},
        "geometry_modes": ["boundary_hints"],
        "boundary_hints": [],
    }
    try:
        validate_era_geometry_pack(bad)
        raised = False
    except Exception:
        raised = True
    assert raised


def test_cli_list_validate_apply(tmp_path: Path, capsys):
    assert main(["era-geometry", "list"]) == 0
    out = capsys.readouterr().out
    assert "we-1444-v1" in out

    assert main(["era-geometry", "validate", "--pack", "we-1444-v1"]) == 0
    assert "valid" in capsys.readouterr().out.lower()

    provinces = tmp_path / "provinces.geojson"
    sample = (
        PROJECT_ROOT
        / "samples"
        / "beta-license-audited"
        / "sample"
        / "provinces.geojson"
    )
    provinces.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")
    out_dir = tmp_path / "applied"
    assert (
        main(
            [
                "era-geometry",
                "apply",
                "--pack",
                "we-1444-v1",
                "--province-input",
                str(provinces),
                "--output-dir",
                str(out_dir),
                "--format",
                "json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["pack_id"] == "we-1444-v1"
    assert payload["province_count_out"] == 7
    assert (out_dir / "provinces.geojson").is_file()


def test_accuracy_label_period_geometry_scope():
    label = accuracy_label(
        geometry_tier=QUALITY_TIER_PERIOD_GEOMETRY,
        politics_tier="curated-politics",
        scenarios=("official-1444",),
        release_channel="beta",
    )
    assert label["geometry_quality_tier"] == "period-geometry"
    joined = " ".join(label["honest_statements"])
    assert "priority-region" in joined or "priority region" in joined
    do_not = " ".join(label["do_not_claim"])
    assert "worldwide" in do_not


def test_committed_sample_and_demo_assets_exist():
    sample_dir = PROJECT_ROOT / "samples" / "era-geometry-we-1444"
    for name in (
        "provinces.geojson",
        "boundary_hints.geojson",
        "lineage.json",
        "lineage.csv",
        "quality_scope.json",
        "era_geometry_manifest.json",
        "README.md",
    ):
        assert (sample_dir / name).is_file(), name

    demo = PROJECT_ROOT / "landing" / "demo" / "data"
    for name in (
        "official-1444-period.geojson",
        "official-1444-period.legend.json",
        "boundary-hints-1444.geojson",
        "lineage-1444.json",
        "demo-manifest.json",
    ):
        assert (demo / name).is_file(), name

    manifest = json.loads((demo / "demo-manifest.json").read_text(encoding="utf-8"))
    s1444 = next(s for s in manifest["scenarios"] if s["id"] == "official-1444")
    assert s1444["supports_period_geometry"] is True
    assert s1444["period_geojson"] == "official-1444-period.geojson"
    live_ids = {layer["id"] for layer in manifest["live_layers"]}
    assert "period-geometry" in live_ids
    assert "boundary-hints" in live_ids
    future_ids = {slot["id"] for slot in manifest["future_slots"]}
    assert "period-geometry" not in future_ids
    assert "boundary-hints" not in future_ids

    period = json.loads((demo / "official-1444-period.geojson").read_text(encoding="utf-8"))
    assert len(period["features"]) == 7
    assert period["gpm"]["geometry_tier"] == "period-geometry"


def test_schema_lineage_validator_rejects_bad_count():
    try:
        validate_era_geometry_lineage(
            {
                "schema_version": "0.1.0",
                "document_type": "era-geometry-lineage",
                "pack_id": "x",
                "era": "1444",
                "row_count": 2,
                "rows": [
                    {
                        "era_province_id": "a",
                        "scaffold_province_id": "a",
                        "operation": "identity",
                    }
                ],
            }
        )
        raised = False
    except SchemaValidationError:
        raised = True
    assert raised
