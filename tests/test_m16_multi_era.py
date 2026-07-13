"""M16: multi-era geometry + politics packs, official-1936, migration notes."""

from __future__ import annotations

import json
from pathlib import Path

from gpm.cli import main
from gpm.era_geometry import list_era_geometry_packs, load_era_geometry_pack
from gpm.multi_era import (
    build_migration_document,
    build_multi_era_pack,
    list_multi_era_packs,
    load_multi_era_pack,
    migration_markdown,
    validate_multi_era_pack,
)
from gpm.paths import (
    ERA_GEOMETRY_DIR,
    MULTI_ERA_DIR,
    SCENARIO_DIR,
    SCENARIO_GOLDEN_DIR,
)
from gpm.release.quality import (
    QUALITY_TIER_CURATED_POLITICS,
    QUALITY_TIER_PERIOD_GEOMETRY,
    accuracy_label,
)
from gpm.scenarios import (
    list_scenarios,
    load_scenario,
    resolve_ownership_records,
    validate_scenario_document,
)
from gpm.schemas import (
    validate_multi_era_migration_notes,
    validate_multi_era_pack as schema_validate_multi_era,
    validate_scenario_definition,
)


def _land(province_id, *, country="FRA", region="FR-01", name=None):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        },
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


def test_bundled_multi_era_pack_validates():
    packs = list_multi_era_packs()
    by_id = {p.pack_id: p for p in packs}
    assert "we-multi-era-v1" in by_id
    summary = by_id["we-multi-era-v1"]
    assert summary.era_count >= 2
    assert "1444" in summary.eras
    assert "1836" in summary.eras
    assert "1936" in summary.eras
    assert "official-1444" in summary.scenario_ids
    assert "official-1836" in summary.scenario_ids
    assert "official-1936" in summary.scenario_ids
    assert "we-1444-v1" in summary.era_geometry_pack_ids
    assert "we-1836-v1" in summary.era_geometry_pack_ids
    assert "we-1936-v1" in summary.era_geometry_pack_ids
    assert summary.region_matrix_row_count >= 2

    document = load_multi_era_pack("we-multi-era-v1")
    validate_multi_era_pack(document)
    schema_validate_multi_era(document)
    assert (MULTI_ERA_DIR / "we-multi-era-v1.json").is_file()


def test_bundled_1836_and_1936_geometry_packs():
    packs = {p.pack_id: p for p in list_era_geometry_packs()}
    assert "we-1836-v1" in packs
    assert "we-1936-v1" in packs
    assert packs["we-1836-v1"].era == "1836"
    assert packs["we-1836-v1"].scenario_id == "official-1836"
    assert packs["we-1836-v1"].quality_tier == "period-geometry"
    assert packs["we-1936-v1"].era == "1936"
    assert packs["we-1936-v1"].scenario_id == "official-1936"
    for pack_id in ("we-1836-v1", "we-1936-v1"):
        document = load_era_geometry_pack(pack_id)
        assert document["geometry_modes"]
        assert document["boundary_hints"]
        assert document["hard_overrides"]
        assert (ERA_GEOMETRY_DIR / f"{pack_id}.json").is_file()


def test_official_1936_bundled_metadata_and_schema():
    scenario = load_scenario("official-1936")
    assert scenario["scenario_id"] == "official-1936"
    assert scenario["era"] == "1936"
    assert scenario["start_date"] == "1936-01-01"
    assert scenario["quality_tier"] == "curated-politics"
    assert scenario["official_era"] is True
    assert scenario["recommended_profile"] == "hoi-like"
    assert "europe" in scenario["priority_theaters"]
    assert "contested-interwar" in scenario["priority_theaters"]
    assert len(scenario["countries"]) >= 40
    assert len(scenario["country_rules"]) >= 50
    assert len(scenario["region_rules"]) >= 50
    region_ids = {rule["match_parent_region_id"] for rule in scenario["region_rules"]}
    assert "DE-NW" in region_ids  # Rhineland
    assert "AT-9" in region_ids  # Vienna (pre-Anschluss Austria)
    assert "CN-21" in region_ids  # Manchukuo
    owners = {rule["owner"] for rule in scenario["country_rules"]}
    assert {"GER", "FRA", "ENG", "ITA", "SOV", "USA", "JAP", "CHI"} <= owners
    validate_scenario_document(scenario)
    validate_scenario_definition(scenario)

    summaries = list_scenarios()
    by_id = {item.scenario_id: item for item in summaries}
    assert "official-1936" in by_id
    summary = by_id["official-1936"]
    assert summary.quality_tier == "curated-politics"
    assert summary.official_era is True
    assert summary.recommended_profile == "hoi-like"


def test_official_1936_golden_file_exists():
    path = SCENARIO_GOLDEN_DIR / "official-1936.json"
    assert path.is_file()
    golden = json.loads(path.read_text(encoding="utf-8"))
    assert golden["scenario_id"] == "official-1936"
    mins = golden["min_owner_counts"]
    assert mins["GER"] >= 10
    assert mins["SOV"] >= 10
    assert mins["JAP"] >= 5
    assert mins["MAN"] >= 1


def test_interwar_theaters_resolve():
    scenario = load_scenario("official-1936")
    features = [
        _land("de_rhine", country="DEU", region="DE-NW"),
        _land("at_vienna", country="AUT", region="AT-9"),
        _land("cz_prague", country="CZE", region="CZ-10"),
        _land("cz_sudeten", country="CZE", region="CZ-42"),
        _land("cn_liaoning", country="CHN", region="CN-21"),
        _land("fr_paris", country="FRA", region="FR-IDF"),
        _land("eth_addis", country="ETH", region="ET-AA"),
        _land("pl_pomerania", country="POL", region="PL-PM"),
    ]
    records, stats = resolve_ownership_records(scenario, features)
    by_id = {row["province_id"]: row for row in records}
    assert by_id["de_rhine"]["owner"] == "GER"
    assert by_id["at_vienna"]["owner"] == "AUS"
    assert by_id["cz_prague"]["owner"] == "CZE"
    assert by_id["cz_sudeten"]["owner"] == "CZE"
    assert by_id["cz_sudeten"]["disputed"] is True
    assert "GER" in (by_id["cz_sudeten"].get("claims") or [])
    assert by_id["cn_liaoning"]["owner"] == "MAN"
    assert by_id["fr_paris"]["owner"] == "FRA"
    assert by_id["eth_addis"]["owner"] == "ETH"
    assert by_id["eth_addis"]["disputed"] is True
    assert by_id["pl_pomerania"]["owner"] == "POL"
    assert stats["region_rule_hits"] >= 6


def test_migration_document_and_markdown():
    pack = load_multi_era_pack("we-multi-era-v1")
    migration = build_migration_document(pack)
    validate_multi_era_migration_notes(migration)
    assert migration["document_type"] == "multi-era-migration-notes"
    assert migration["pack_id"] == "we-multi-era-v1"
    assert len(migration["eras"]) >= 3
    assert migration["consumer_guidance"]
    assert migration["cross_era_join"]["recommended_key"] == "scaffold_province_id"
    md = migration_markdown(migration)
    assert "Migration notes" in md
    assert "we-multi-era-v1" in md
    assert "Region quality matrix" in md
    assert "1444" in md and "1936" in md


def test_build_multi_era_pack_on_fixture(tmp_path: Path):
    provinces = tmp_path / "provinces.geojson"
    _write_provinces(
        provinces,
        [
            _land(
                "sample_de_rhineland",
                country="DEU",
                region="DE-NW",
                name="Rhineland",
            ),
            _land(
                "sample_be_flanders",
                country="BEL",
                region="BE-VLG",
                name="Flanders",
            ),
            _land("sample_fr_paris", country="FRA", region="FR-IDF", name="Paris"),
            _land(
                "sample_fr_normandy",
                country="FRA",
                region="FR-NOR",
                name="Normandy",
            ),
            _land(
                "sample_nl_holland",
                country="NLD",
                region="NL-NH",
                name="Holland",
            ),
            _land("sample_lu_core", country="LUX", region="LU-LU", name="Luxembourg"),
        ],
    )
    out = tmp_path / "multi_era_out"
    result = build_multi_era_pack(
        "we-multi-era-v1",
        province_input=provinces,
        output_dir=out,
        profile_id="modern-small",
        recompute_adjacency=False,
    )
    assert result.pack_id == "we-multi-era-v1"
    assert result.era_count == 3
    assert Path(result.manifest_output).is_file()
    assert Path(result.migration_md).is_file()
    assert Path(result.migration_json).is_file()
    assert (out / "region_quality_matrix.json").is_file()
    assert (out / "eras" / "1444" / "geometry" / "provinces.geojson").is_file()
    assert (out / "eras" / "1836" / "politics" / "ownership.json").is_file()
    assert (out / "eras" / "1936" / "politics" / "ownership.csv").is_file()
    # 1444 split should produce extra province from Rhineland.
    fc_1444 = json.loads(
        (out / "eras" / "1444" / "geometry" / "provinces.geojson").read_text(
            encoding="utf-8"
        )
    )
    ids_1444 = {
        f["properties"]["province_id"] for f in fc_1444["features"]
    }
    assert "era_de_cologne" in ids_1444 or "sample_de_rhineland" in ids_1444


def test_accuracy_label_notes_official_1936():
    label = accuracy_label(
        scenarios=("official-1936", "modern-baseline"),
        politics_tier=QUALITY_TIER_CURATED_POLITICS,
        geometry_tier=QUALITY_TIER_PERIOD_GEOMETRY,
        profile_id="hoi-like",
    )
    assert label["politics_quality_tier"] == "curated-politics"
    assert any("official-1936" in note for note in label["scenario_notes"])
    assert any("interwar" in note.lower() or "1936" in note for note in label["scenario_notes"])


def test_cli_multi_era_list_validate_migration(capsys, tmp_path: Path):
    assert main(["multi-era", "list"]) == 0
    listed = capsys.readouterr().out
    assert "we-multi-era-v1" in listed
    assert "1936" in listed

    assert main(["multi-era", "validate", "--pack", "we-multi-era-v1"]) == 0
    validated = capsys.readouterr().out
    assert "is valid" in validated

    assert (
        main(
            [
                "multi-era",
                "migration",
                "--pack",
                "we-multi-era-v1",
                "--output-dir",
                str(tmp_path),
            ]
        )
        == 0
    )
    assert (tmp_path / "migration_notes.json").is_file()
    assert (tmp_path / "MIGRATION.md").is_file()


def test_cli_scenario_list_includes_1936(capsys):
    assert main(["scenario", "list"]) == 0
    listed = capsys.readouterr().out
    assert "official-1936" in listed
    assert "curated-politics" in listed


def test_sample_multi_era_artifacts_exist():
    sample = Path("samples/multi-era-we-v1")
    assert sample.is_dir()
    assert (sample / "MIGRATION.md").is_file()
    assert (sample / "multi_era_manifest.json").is_file()
    assert (sample / "region_quality_matrix.json").is_file()
    assert (sample / "eras" / "1936" / "era_manifest.json").is_file()


def test_demo_manifest_ships_1936_and_multi_era():
    manifest = json.loads(
        Path("landing/demo/data/demo-manifest.json").read_text(encoding="utf-8")
    )
    scenario_ids = {s["id"] for s in manifest["scenarios"]}
    assert "official-1936" in scenario_ids
    assert "official-1836" in scenario_ids
    live_ids = {s["id"] for s in manifest.get("live_layers") or []}
    assert "multi-era-packs" in live_ids
    future_ids = {s["id"] for s in manifest.get("future_slots") or []}
    assert "multi-era-packs" not in future_ids
    assert "era-1936" not in future_ids
    for sid in ("official-1444", "official-1836", "official-1936"):
        meta = next(s for s in manifest["scenarios"] if s["id"] == sid)
        assert meta["supports_period_geometry"] is True
        assert meta.get("period_geojson")
        assert meta.get("boundary_hints")
        # PMTiles-first (M22): no full global GeoJSON ships per scenario.
        assert meta["geojson"] is None
        assert Path("landing/demo/data", meta["pmtiles"]).is_file()
        assert Path("landing/demo/data", meta["period_geojson"]).is_file()


def test_scenario_definition_file_present():
    assert (SCENARIO_DIR / "official-1936.json").is_file()
