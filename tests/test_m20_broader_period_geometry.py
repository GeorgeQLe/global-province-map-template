"""M20: broader period geometry beyond Western Europe (Central Europe + compose)."""

from __future__ import annotations

import json
from pathlib import Path

from gpm.cli import main
from gpm.era_geometry import (
    apply_era_geometry_pack,
    apply_era_geometry_packs,
    list_era_geometry_packs,
    load_era_geometry_pack,
    validate_era_geometry_pack,
)
from gpm.multi_era import (
    build_multi_era_pack,
    list_multi_era_packs,
    load_multi_era_pack,
    resolve_era_geometry_pack_ids,
    validate_multi_era_pack,
)
from gpm.paths import ERA_GEOMETRY_DIR, MULTI_ERA_DIR, PROJECT_ROOT
from gpm.schemas import (
    validate_era_geometry_pack as schema_validate_pack,
    validate_multi_era_pack as schema_validate_multi_era,
)


def _land(province_id, *, country="CZE", region="CZ-01", name=None, coords=None):
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


def test_bundled_ce_packs_validate():
    packs = {p.pack_id: p for p in list_era_geometry_packs()}
    for pack_id, era, scenario in (
        ("ce-1444-v1", "1444", "official-1444"),
        ("ce-1836-v1", "1836", "official-1836"),
        ("ce-1936-v1", "1936", "official-1936"),
    ):
        assert pack_id in packs
        summary = packs[pack_id]
        assert summary.era == era
        assert summary.scenario_id == scenario
        assert summary.quality_tier == "period-geometry"
        assert summary.priority_region_id == "central-europe"
        assert "boundary_hints" in summary.geometry_modes
        assert "hard_overrides" in summary.geometry_modes
        assert summary.boundary_hint_count >= 3
        assert summary.hard_override_count >= 3

        document = load_era_geometry_pack(pack_id)
        validate_era_geometry_pack(document)
        schema_validate_pack(document)
        assert document["priority_region"]["parent_country_ids"] == [
            "AUT",
            "CZE",
            "POL",
            "HUN",
        ]
        assert (ERA_GEOMETRY_DIR / f"{pack_id}.json").is_file()


def test_apply_ce_1444_split_and_hints(tmp_path: Path):
    provinces = tmp_path / "provinces.geojson"
    _write_provinces(
        provinces,
        [
            _land(
                "sample_cz_bohemia",
                country="CZE",
                region="CZ-ST",
                name="Bohemia",
                coords=[[14.0, 48.8], [16.0, 48.8], [16.0, 50.5], [14.0, 50.5], [14.0, 48.8]],
            ),
            _land(
                "sample_hu_pannon",
                country="HUN",
                region="HU-BU",
                name="Pannonia",
                coords=[[17.5, 47.0], [19.5, 47.0], [19.5, 47.8], [17.5, 47.8], [17.5, 47.0]],
            ),
            _land(
                "sample_at_vienna",
                country="AUT",
                region="AT-9",
                name="Vienna",
                coords=[[15.5, 48.0], [16.8, 48.0], [16.8, 48.8], [15.5, 48.8], [15.5, 48.0]],
            ),
            _land(
                "sample_fr_paris",
                country="FRA",
                region="FR-IDF",
                name="Paris",
            ),
        ],
    )
    out = tmp_path / "ce1444"
    result = apply_era_geometry_pack(
        "ce-1444-v1",
        province_input=provinces,
        output_dir=out,
    )
    assert result.hard_override_applied >= 3
    assert result.boundary_hint_count >= 4
    assert result.province_count_out == 5  # split +3 others → 5

    fc = json.loads(Path(result.provinces_output).read_text(encoding="utf-8"))
    ids = {f["properties"]["province_id"] for f in fc["features"]}
    assert "era_cz_prague" in ids
    assert "era_cz_bohemia_residual" in ids
    assert "era_hu_pannon" in ids
    assert "sample_cz_bohemia" not in ids

    hints = json.loads(Path(result.boundary_hints_output).read_text(encoding="utf-8"))
    hint_ids = {f["properties"]["hint_id"] for f in hints["features"]}
    assert "ce1444-bohemian-crown" in hint_ids
    assert "ce1444-ottoman-hungarian" in hint_ids

    lineage = json.loads(Path(result.lineage_json_output).read_text(encoding="utf-8"))
    by_era = {r["era_province_id"]: r for r in lineage["rows"]}
    assert by_era["era_cz_prague"]["operation"] == "split_child"
    assert by_era["era_cz_prague"]["scaffold_province_id"] == "sample_cz_bohemia"


def test_compose_we_and_ce_packs(tmp_path: Path):
    scaffold = PROJECT_ROOT / "samples" / "scaffold-we-ce" / "provinces.geojson"
    assert scaffold.is_file()
    out = tmp_path / "composed"
    result = apply_era_geometry_packs(
        ["we-1444-v1", "ce-1444-v1"],
        province_input=scaffold,
        output_dir=out,
    )
    assert result.boundary_hint_count >= 8  # WE + CE hints merged
    assert result.hard_override_applied >= 6
    assert "central-europe" in result.priority_region_id
    assert "western-europe" in result.priority_region_id or "+" in result.pack_id

    fc = json.loads(Path(result.provinces_output).read_text(encoding="utf-8"))
    ids = {f["properties"]["province_id"] for f in fc["features"]}
    # WE split
    assert "era_de_cologne" in ids
    assert "era_de_rhineland_residual" in ids
    # CE split
    assert "era_cz_prague" in ids
    assert "era_cz_bohemia_residual" in ids
    assert "era_hu_pannon" in ids

    lineage = json.loads(Path(result.lineage_json_output).read_text(encoding="utf-8"))
    by_era = {r["era_province_id"]: r for r in lineage["rows"]}
    # WE hard work not clobbered by CE pass-through
    assert by_era["era_de_cologne"]["operation"] == "split_child"
    assert by_era["era_de_cologne"]["scaffold_province_id"] == "sample_de_rhineland"
    assert by_era["era_cz_prague"]["scaffold_province_id"] == "sample_cz_bohemia"

    hints = json.loads(Path(result.boundary_hints_output).read_text(encoding="utf-8"))
    packs = {f["properties"].get("pack_id") for f in hints["features"]}
    assert "we-1444-v1" in packs
    assert "ce-1444-v1" in packs


def test_europe_multi_era_pack_validates_and_builds(tmp_path: Path):
    packs = {p.pack_id: p for p in list_multi_era_packs()}
    assert "europe-multi-era-v1" in packs
    summary = packs["europe-multi-era-v1"]
    assert summary.era_count == 3
    assert "ce-1444-v1" in summary.era_geometry_pack_ids
    assert "we-1444-v1" in summary.era_geometry_pack_ids
    assert summary.region_matrix_row_count >= 5

    document = load_multi_era_pack("europe-multi-era-v1")
    validate_multi_era_pack(document)
    schema_validate_multi_era(document)
    assert (MULTI_ERA_DIR / "europe-multi-era-v1.json").is_file()
    assert len(document.get("priority_regions") or []) >= 2

    for slot in document["eras"]:
        ids = resolve_era_geometry_pack_ids(slot)
        assert len(ids) == 2
        assert ids[0].startswith("we-")
        assert ids[1].startswith("ce-")

    scaffold = PROJECT_ROOT / "samples" / "scaffold-we-ce" / "provinces.geojson"
    result = build_multi_era_pack(
        "europe-multi-era-v1",
        province_input=scaffold,
        output_dir=tmp_path / "europe",
        profile_id="modern-small",
    )
    assert result.era_count == 3
    assert "ce-1444-v1" in result.era_geometry_pack_ids
    matrix = json.loads(
        (tmp_path / "europe" / "region_quality_matrix.json").read_text(encoding="utf-8")
    )
    region_ids = {row["region_id"] for row in matrix["rows"]}
    assert "western-europe" in region_ids
    assert "central-europe" in region_ids
    for row in matrix["rows"]:
        if row["region_id"] in {"western-europe", "central-europe"}:
            for era in ("1444", "1836", "1936"):
                assert row["by_era"][era]["geometry"] == "period-geometry"

    for era in ("1444", "1836", "1936"):
        geom = tmp_path / "europe" / "eras" / era / "geometry" / "provinces.geojson"
        assert geom.is_file()
        hints = tmp_path / "europe" / "eras" / era / "geometry" / "boundary_hints.geojson"
        assert hints.is_file()
        hint_fc = json.loads(hints.read_text(encoding="utf-8"))
        assert len(hint_fc["features"]) >= 6


def test_cli_lists_ce_and_europe_packs():
    assert main(["era-geometry", "list"]) == 0
    assert main(["multi-era", "list"]) == 0
    assert main(["era-geometry", "validate", "--pack", "ce-1444-v1"]) == 0
    assert main(["multi-era", "validate", "--pack", "europe-multi-era-v1"]) == 0


def test_committed_samples_exist():
    scaffold = PROJECT_ROOT / "samples" / "scaffold-we-ce" / "provinces.geojson"
    assert scaffold.is_file()
    features = json.loads(scaffold.read_text(encoding="utf-8"))["features"]
    countries = {f["properties"]["parent_country_id"] for f in features}
    assert {"FRA", "DEU", "AUT", "CZE", "POL", "HUN"}.issubset(countries)

    ce_sample = PROJECT_ROOT / "samples" / "era-geometry-ce-1444" / "provinces.geojson"
    assert ce_sample.is_file()
    europe = PROJECT_ROOT / "samples" / "multi-era-europe-v1"
    assert (europe / "multi_era_manifest.json").is_file()
    assert (europe / "region_quality_matrix.json").is_file()
    assert (europe / "MIGRATION.md").is_file()
    for era in ("1444", "1836", "1936"):
        assert (europe / "eras" / era / "geometry" / "provinces.geojson").is_file()
