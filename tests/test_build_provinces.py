import json
import struct
import zipfile
from pathlib import Path

from gpm.builders.provinces import build_land_province_draft
from gpm.cli import main


def test_build_land_province_draft_creates_candidates_and_processed_provinces(tmp_path):
    raw_dir = _write_natural_earth_fixture(tmp_path)
    intermediate_dir = tmp_path / "intermediate"
    processed_dir = tmp_path / "processed"

    result = build_land_province_draft(
        "modern-small",
        raw_dir=raw_dir,
        intermediate_dir=intermediate_dir,
        processed_dir=processed_dir,
    )

    assert result.province_count == 2
    assert result.admin1_count == 1
    assert result.admin0_fallback_count == 1
    assert Path(result.candidate_output).is_file()
    assert Path(result.province_output).is_file()

    provinces = json.loads(Path(result.province_output).read_text(encoding="utf-8"))
    assert provinces["type"] == "FeatureCollection"
    assert provinces["gpm"]["profile_id"] == "modern-small"
    assert provinces["gpm"]["id_scheme"] == "source-geometry-sha256-v1"
    assert provinces["name"] == "provinces"
    assert len(provinces["features"]) == 2

    properties = [feature["properties"] for feature in provinces["features"]]
    assert {item["source_layer"] for item in properties} == {
        "admin1_states_provinces",
        "admin0_countries",
    }
    assert all(item["kind"] == "land" for item in properties)
    assert all(item["area_sq_km"] > 0 for item in properties)
    assert all(item["source_lineage"] for item in properties)
    assert all(item["license_lineage"] == ["Natural Earth public domain"] for item in properties)
    assert [item["province_id"] for item in properties] == sorted(
        item["province_id"] for item in properties
    )

    candidates = json.loads(Path(result.candidate_output).read_text(encoding="utf-8"))
    assert candidates["name"] == "land_province_candidates"
    assert all("candidate_id" in feature["properties"] for feature in candidates["features"])


def test_build_provinces_cli_writes_json_summary(tmp_path, capsys):
    raw_dir = _write_natural_earth_fixture(tmp_path)
    candidate_output = tmp_path / "candidate.geojson"
    province_output = tmp_path / "province.geojson"

    assert (
        main(
            [
                "build",
                "provinces",
                "--raw-dir",
                str(raw_dir),
                "--candidate-output",
                str(candidate_output),
                "--province-output",
                str(province_output),
                "--format",
                "json",
            ]
        )
        == 0
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary["province_count"] == 2
    assert summary["candidate_output"] == str(candidate_output)
    assert province_output.is_file()


def test_build_provinces_cli_reports_missing_raw_artifacts(tmp_path, capsys):
    assert main(["build", "provinces", "--raw-dir", str(tmp_path / "missing")]) == 1
    captured = capsys.readouterr()

    assert "requires downloaded Natural Earth admin boundary zips" in captured.err
    assert "ne_10m_admin_1_states_provinces.zip" in captured.err
    assert "Traceback" not in captured.err


def test_build_provinces_cli_applies_m4_population_refinement(tmp_path, capsys):
    raw_dir = _write_natural_earth_fixture(tmp_path)
    population_input = tmp_path / "population.geojson"
    population_input.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "gpm": {
                    "source_lineage": ["worldpop:test"],
                    "license_lineage": ["WorldPop CC BY 4.0 test fixture"],
                },
                "features": [
                    {
                        "type": "Feature",
                        "id": "dense",
                        "geometry": {"type": "Point", "coordinates": [0.2, 0.5]},
                        "properties": {"population": 1_000},
                    },
                    {
                        "type": "Feature",
                        "id": "sparse",
                        "geometry": {"type": "Point", "coordinates": [2.5, 0.5]},
                        "properties": {"population": 10},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    province_output = tmp_path / "provinces.geojson"

    assert (
        main(
            [
                "build",
                "provinces",
                "--profile",
                "victoria-like",
                "--raw-dir",
                str(raw_dir),
                "--population-input",
                str(population_input),
                "--target-province-count",
                "4",
                "--province-output",
                str(province_output),
                "--candidate-output",
                str(tmp_path / "candidates.geojson"),
                "--format",
                "json",
            ]
        )
        == 0
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary["refinement_applied"] is True
    assert summary["province_count"] == 4
    assert summary["split_count"] == 2
    assert summary["population_total"] == 1_010
    provinces = json.loads(province_output.read_text(encoding="utf-8"))
    assert provinces["gpm"]["refinement"]["milestone"] == "M4"
    assert provinces["gpm"]["refinement"]["population_total"] == 1_010
    assert sum(
        feature["properties"]["estimated_population"] for feature in provinces["features"]
    ) == 1_010


def test_build_provinces_cli_rejects_refinement_target_below_candidates(tmp_path, capsys):
    raw_dir = _write_natural_earth_fixture(tmp_path)

    assert (
        main(
            [
                "build",
                "provinces",
                "--raw-dir",
                str(raw_dir),
                "--target-province-count",
                "1",
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "below the 2 source province count" in captured.err
    assert "Traceback" not in captured.err


def _write_natural_earth_fixture(tmp_path) -> Path:
    raw_dir = tmp_path / "raw"
    natural_earth_dir = raw_dir / "natural_earth"
    natural_earth_dir.mkdir(parents=True)

    _write_polygon_zip(
        natural_earth_dir / "ne_10m_admin_1_states_provinces.zip",
        "ne_10m_admin_1_states_provinces",
        [
            (
                {
                    "name": "North Example",
                    "name_en": "North Example",
                    "adm0_a3": "AAA",
                    "iso_3166_2": "AAA-NE",
                },
                [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]],
            )
        ],
    )
    _write_polygon_zip(
        natural_earth_dir / "ne_10m_admin_0_countries.zip",
        "ne_10m_admin_0_countries",
        [
            (
                {
                    "name": "Exampleland",
                    "name_en": "Exampleland",
                    "adm0_a3": "AAA",
                    "iso_a3": "AAA",
                    "pop_est": "100",
                },
                [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]],
            ),
            (
                {
                    "name": "Fallbackia",
                    "name_en": "Fallbackia",
                    "adm0_a3": "BBB",
                    "iso_a3": "BBB",
                    "pop_est": "250",
                },
                [[2.0, 0.0], [3.0, 0.0], [3.0, 1.0], [2.0, 1.0], [2.0, 0.0]],
            ),
        ],
    )
    return raw_dir


def _write_polygon_zip(path: Path, basename: str, records: list[tuple[dict[str, str], list[list[float]]]]) -> None:
    shp_bytes = _shp_bytes([ring for _, ring in records])
    dbf_bytes = _dbf_bytes([properties for properties, _ in records])
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{basename}.shp", shp_bytes)
        archive.writestr(f"{basename}.dbf", dbf_bytes)


def _shp_bytes(rings: list[list[list[float]]]) -> bytes:
    record_payloads = [_polygon_record(ring) for ring in rings]
    file_length_words = (100 + sum(8 + len(payload) for payload in record_payloads)) // 2
    bounds = _bounds([point for ring in rings for point in ring])

    header = bytearray(100)
    struct.pack_into(">i", header, 0, 9994)
    struct.pack_into(">i", header, 24, file_length_words)
    struct.pack_into("<i", header, 28, 1000)
    struct.pack_into("<i", header, 32, 5)
    struct.pack_into("<4d", header, 36, *bounds)

    records = bytearray()
    for index, payload in enumerate(record_payloads, start=1):
        records.extend(struct.pack(">2i", index, len(payload) // 2))
        records.extend(payload)
    return bytes(header + records)


def _polygon_record(ring: list[list[float]]) -> bytes:
    bounds = _bounds(ring)
    payload = bytearray()
    payload.extend(struct.pack("<i", 5))
    payload.extend(struct.pack("<4d", *bounds))
    payload.extend(struct.pack("<2i", 1, len(ring)))
    payload.extend(struct.pack("<i", 0))
    for x, y in ring:
        payload.extend(struct.pack("<2d", x, y))
    return bytes(payload)


def _dbf_bytes(records: list[dict[str, str]]) -> bytes:
    field_names = sorted({key for record in records for key in record})
    field_length = 40
    header_length = 32 + (32 * len(field_names)) + 1
    record_length = 1 + (field_length * len(field_names))

    header = bytearray(32)
    header[0] = 0x03
    header[1:4] = bytes([126, 7, 9])
    struct.pack_into("<I", header, 4, len(records))
    struct.pack_into("<H", header, 8, header_length)
    struct.pack_into("<H", header, 10, record_length)

    fields = bytearray()
    for name in field_names:
        descriptor = bytearray(32)
        descriptor[0:11] = name.encode("ascii")[:11].ljust(11, b"\x00")
        descriptor[11] = ord("C")
        descriptor[16] = field_length
        fields.extend(descriptor)
    fields.append(0x0D)

    rows = bytearray()
    for record in records:
        rows.extend(b" ")
        for name in field_names:
            value = record.get(name, "").encode("ascii")[:field_length]
            rows.extend(value.ljust(field_length, b" "))
    rows.append(0x1A)

    return bytes(header + fields + rows)


def _bounds(points: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)
