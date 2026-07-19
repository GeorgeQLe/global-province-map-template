import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator

from gpm.cli import main
from gpm.historical.casebook import load_casebook
from gpm.runtime import RuntimeCompileError, RuntimeLoadError, RuntimePack, compile_runtime_pack
from gpm.schemas import validate_runtime_pack_manifest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASEBOOK = PROJECT_ROOT / "tests" / "fixtures" / "m25a" / "casebook.json"


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_runtime_manifest_schema_is_valid():
    schema = json.loads((PROJECT_ROOT / "schemas" / "runtime-pack.schema.json").read_text())
    Draft202012Validator.check_schema(schema)


def test_casebook_compiles_byte_identically_and_loads_every_hard_case(tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    first = compile_runtime_pack(CASEBOOK, left, pack_id="m25b-reference", max_zoom=1)
    second = compile_runtime_pack(CASEBOOK, right, pack_id="m25b-reference", max_zoom=1)

    assert _hashes(left) == _hashes(right)
    assert first.province_count == second.province_count == 10
    assert first.scenario_count == second.scenario_count == 8
    manifest = json.loads((left / "runtime_manifest.json").read_text())
    validate_runtime_pack_manifest(manifest)
    assert manifest["deterministic"] is True
    assert manifest["counts"]["graph_edges"]["land"] == 1
    assert manifest["counts"]["triangles_by_lod"]["0"] >= first.component_count

    pack = RuntimePack(left)
    casebook = load_casebook(CASEBOOK)
    for case in casebook["cases"]:
        statuses = pack.scenario_statuses(case["fixture_id"])
        actual = {(row["subject_id"], row["relationship"], row["actor_political_unit_id"]) for row in statuses}
        expected = {(row["subject_id"], row["relationship"], row["actor_political_unit_id"]) for row in case["canonical"]["statuses"]}
        assert actual == expected
        assert list(pack.scenario_unions(case["fixture_id"])) == [
            {
                "relationship": row["relationship"],
                "actor_political_unit_id": row["actor_political_unit_id"],
                "member_political_unit_ids": sorted(row["member_political_unit_ids"]),
            }
            for row in case["canonical"].get("union_relationships", [])
        ]
        for stable_id in case["expectations"]["save_migration"]["saved_province_ids"]:
            expected_id = case["expectations"]["save_migration"]["province_id_map"].get(stable_id, stable_id)
            assert pack.migration_target(stable_id) == expected_id


def test_dense_indices_csr_and_revisioned_migrations(tmp_path):
    output = tmp_path / "pack"
    compile_runtime_pack(CASEBOOK, output, compatibility_revision="2", previous_revision="1", max_zoom=0)
    pack = RuntimePack(output)
    stable_id = pack.ids["provinces"][0]
    assert pack.stable_id("provinces", pack.dense_index("provinces", stable_id)) == stable_id
    assert all(isinstance(value, int) for value in pack.neighbors(0))
    assert pack.migration_target("legacy-san-marino", from_revision="1") == "prv-san-marino"
    with pytest.raises(RuntimeLoadError, match="not 0"):
        pack.migration_target("legacy-san-marino", from_revision="0")


def test_loader_rejects_negative_indices_and_unknown_graphs(tmp_path):
    output = tmp_path / "pack"
    compile_runtime_pack(CASEBOOK, output, max_zoom=0)
    pack = RuntimePack(output)
    with pytest.raises(RuntimeLoadError, match="dense index"):
        pack.stable_id("provinces", -1)
    with pytest.raises(RuntimeLoadError, match="scenario dense index"):
        pack.scenario_statuses(-1)
    with pytest.raises(RuntimeLoadError, match="scenario dense index"):
        pack.scenario_unions(-1)
    with pytest.raises(RuntimeLoadError, match="unknown graph"):
        pack.neighbors(0, graph="../core/provinces.bin")


def test_normal_pack_excludes_evidence_debug_symbols_and_meets_fixture_budgets(tmp_path):
    output = tmp_path / "pack"
    compile_runtime_pack(CASEBOOK, output, max_zoom=0)
    manifest = json.loads((output / "runtime_manifest.json").read_text())
    paths = {row["path"] for row in manifest["files"]}
    assert not any(path.startswith("debug/") for path in paths)
    assert manifest["size_metrics"]["core_uncompressed_bytes"] < 16 * 1024 * 1024
    assert manifest["size_metrics"]["core_individually_gzip_bytes"] < 8 * 1024 * 1024
    assert manifest["size_metrics"]["initial_core_plus_lod0_gzip_bytes"] < 8 * 1024 * 1024
    assert manifest["size_metrics"]["geometry_archive_bytes"] < 128 * 1024 * 1024
    assert RuntimePack.benchmark(output, iterations=2)["load_ms"]["p95"] < 1000
    assert RuntimePack.benchmark(output, iterations=2)["tile_read_ms"]["p95"] < 25


def test_loader_rejects_tampering_and_compiler_rejects_nonempty_output(tmp_path):
    output = tmp_path / "pack"
    compile_runtime_pack(CASEBOOK, output, max_zoom=0)
    graph = output / "graphs" / "land.csr"
    graph.write_bytes(graph.read_bytes() + b"corrupt")
    with pytest.raises(RuntimeLoadError, match="hash mismatch"):
        RuntimePack(output)
    with pytest.raises(RuntimeCompileError, match="not empty"):
        compile_runtime_pack(CASEBOOK, output, max_zoom=0)


def test_runtime_cli_compiles_reference_pack(tmp_path, capsys):
    output = tmp_path / "runtime"
    assert main(["export", "runtime", "--canonical-input", str(CASEBOOK), "--output-dir", str(output),
                 "--pack-id", "cli-reference", "--max-zoom", "0", "--benchmark", "--format", "json"]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["pack_id"] == "cli-reference"
    assert summary["benchmark"]["province_count"] == 10
    RuntimePack(output)


def test_reference_builder_runs_from_a_fresh_checkout_environment(tmp_path):
    output = tmp_path / "reference"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "build-m25b-reference.py"),
         "--output-dir", str(output)],
        cwd=tmp_path,
        env=environment,
        check=True,
    )
    RuntimePack(output)
