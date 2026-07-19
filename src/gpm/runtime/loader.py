"""Small dependency-free-at-runtime reference loader for M25B packs."""

from __future__ import annotations

import hashlib
import json
import struct
import time
import tracemalloc
from pathlib import Path
from typing import Any

from gpm.tiles.pmtiles_io import read_pmtiles_tile


class RuntimeLoadError(ValueError):
    """Raised when a runtime pack is corrupt or incompatible."""


class RuntimePack:
    """Verified read-only view of a compiled runtime pack."""

    def __init__(self, root: Path | str, *, verify_hashes: bool = True) -> None:
        self.root = Path(root)
        try:
            self.manifest = json.loads((self.root / "runtime_manifest.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeLoadError(f"cannot read runtime manifest: {exc}") from exc
        if self.manifest.get("pack_type") != "gpm-game-runtime" or self.manifest.get("schema_version") != "1.0.0":
            raise RuntimeLoadError("unsupported runtime pack type or schema version")
        if verify_hashes:
            self.verify()
        self.ids = self._json("core/stable_ids.json")
        self.scenario_index = self._json("scenarios/index.json")
        self._reverse = {kind: {value: index for index, value in enumerate(values)}
                         for kind, values in self.ids.items() if isinstance(values, list)}

    @property
    def compatibility_revision(self) -> str:
        return str(self.manifest["compatibility_revision"])

    def verify(self) -> None:
        for record in self.manifest.get("files", []):
            path = self.root / record["path"]
            if not path.is_file():
                raise RuntimeLoadError(f"runtime asset is missing: {record['path']}")
            data = path.read_bytes()
            if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise RuntimeLoadError(f"runtime asset hash mismatch: {record['path']}")

    def verify_core(self) -> None:
        """Verify startup assets without reading the high-detail geometry archive."""
        prefixes = ("core/", "graphs/", "scenarios/")
        for record in self.manifest.get("files", []):
            if not record["path"].startswith(prefixes) and record["path"] != "migration.json":
                continue
            path = self.root / record["path"]
            data = path.read_bytes()
            if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise RuntimeLoadError(f"runtime asset hash mismatch: {record['path']}")

    def dense_index(self, kind: str, stable_id: str) -> int:
        try:
            return self._reverse[kind][stable_id]
        except KeyError as exc:
            raise RuntimeLoadError(f"unknown {kind} stable ID: {stable_id}") from exc

    def stable_id(self, kind: str, dense_index: int) -> str:
        try:
            values = self.ids[kind]
            if not 0 <= dense_index < len(values):
                raise IndexError(dense_index)
            return values[dense_index]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeLoadError(f"unknown {kind} dense index: {dense_index}") from exc

    def neighbors(self, province: int | str, *, graph: str = "land") -> tuple[int, ...]:
        if graph not in {"land", "sea", "strait", "port"}:
            raise RuntimeLoadError(f"unknown graph: {graph}")
        index = self.dense_index("provinces", province) if isinstance(province, str) else province
        path = self.root / "graphs" / f"{graph}.csr"
        data = path.read_bytes()
        if data[:8] != b"GPMCSR1\0":
            raise RuntimeLoadError(f"invalid CSR graph: {graph}")
        node_count, edge_count = struct.unpack_from("<II", data, 8)
        if not 0 <= index < node_count:
            raise RuntimeLoadError(f"province dense index outside graph: {index}")
        offsets = struct.unpack_from(f"<{node_count + 1}I", data, 16)
        start, end = offsets[index], offsets[index + 1]
        base = 16 + 4 * (node_count + 1)
        all_neighbors = struct.unpack_from(f"<{edge_count}I", data, base) if edge_count else ()
        return tuple(all_neighbors[start:end])

    def scenario_statuses(self, scenario: int | str = 0) -> tuple[dict[str, Any], ...]:
        """Decode a scenario's status state by applying its delta to the base."""
        scenarios = self.scenario_index["scenarios"]
        if isinstance(scenario, str):
            try:
                meta = next(item for item in scenarios if item["scenario_id"] == scenario)
            except StopIteration as exc:
                raise RuntimeLoadError(f"unknown scenario: {scenario}") from exc
        else:
            try:
                if not 0 <= scenario < len(scenarios):
                    raise IndexError(scenario)
                meta = scenarios[scenario]
            except (IndexError, TypeError) as exc:
                raise RuntimeLoadError(f"unknown scenario dense index: {scenario}") from exc
        base_meta = scenarios[0]
        rows = set(self._status_table(base_meta["path"]))
        if meta["mode"] == "delta":
            removed, added = self._status_delta(meta["path"])
            rows.difference_update(removed)
            rows.update(added)
        kinds = ("components", "provinces", "political_units")
        decoded = []
        for kind, relation, _, subject, actor in sorted(rows):
            decoded.append({
                "subject_kind": kinds[kind],
                "subject_id": self.ids[kinds[kind]][subject],
                "relationship": self.ids["relationships"][relation],
                "actor_political_unit_id": self.ids["political_units"][actor],
            })
        return tuple(decoded)

    def scenario_unions(self, scenario: int | str = 0) -> tuple[dict[str, Any], ...]:
        """Decode the scenario's political-unit personal-union relationships."""
        scenarios = self.scenario_index["scenarios"]
        if isinstance(scenario, str):
            try:
                meta = next(item for item in scenarios if item["scenario_id"] == scenario)
            except StopIteration as exc:
                raise RuntimeLoadError(f"unknown scenario: {scenario}") from exc
        else:
            try:
                if not 0 <= scenario < len(scenarios):
                    raise IndexError(scenario)
                meta = scenarios[scenario]
            except (IndexError, TypeError) as exc:
                raise RuntimeLoadError(f"unknown scenario dense index: {scenario}") from exc
        data = (self.root / meta["union_path"]).read_bytes()
        if data[:8] != b"GPMUNI1\0":
            raise RuntimeLoadError(f"invalid union table: {meta['union_path']}")
        record_count, member_count = struct.unpack_from("<II", data, 8)
        expected_size = 16 + record_count * 12 + member_count * 4
        if len(data) != expected_size:
            raise RuntimeLoadError(f"invalid union table size: {meta['union_path']}")
        member_base = 16 + record_count * 12
        members = struct.unpack_from(f"<{member_count}I", data, member_base) if member_count else ()
        decoded = []
        for index in range(record_count):
            actor, offset, count = struct.unpack_from("<III", data, 16 + index * 12)
            decoded.append({
                "relationship": "personal_union",
                "actor_political_unit_id": self.ids["political_units"][actor],
                "member_political_unit_ids": [self.ids["political_units"][value] for value in members[offset:offset + count]],
            })
        return tuple(decoded)

    def migration_target(self, saved_province_id: str, *, from_revision: str | None = None) -> str:
        migration = self._json("migration.json")
        if from_revision is not None:
            declared = migration.get("from_compatibility_revision")
            if declared is not None and str(declared) != str(from_revision):
                raise RuntimeLoadError(f"migration is for revision {declared}, not {from_revision}")
        target = migration.get("province_id_map", {}).get(saved_province_id, saved_province_id)
        if target not in self._reverse["provinces"]:
            raise RuntimeLoadError(f"saved province cannot be resolved: {saved_province_id}")
        return target

    @classmethod
    def benchmark(cls, root: Path | str, *, iterations: int = 5) -> dict[str, Any]:
        samples = []
        peaks = []
        tile_samples = []
        for _ in range(max(1, iterations)):
            tracemalloc.start()
            started = time.perf_counter()
            pack = cls(root, verify_hashes=False)
            pack.verify_core()
            for graph in ("land", "sea", "strait", "port"):
                if pack.ids["provinces"]:
                    pack.neighbors(0, graph=graph)
            samples.append((time.perf_counter() - started) * 1000)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peaks.append(peak)
            tile_started = time.perf_counter()
            tile = read_pmtiles_tile(Path(root) / pack.manifest["entrypoints"]["pmtiles"], 0, 0, 0)
            tile_samples.append((time.perf_counter() - tile_started) * 1000)
            if tile is None:
                raise RuntimeLoadError("runtime PMTiles has no lowest-LOD z0 tile")
        ordered = sorted(samples)
        p95_index = min(len(ordered) - 1, int(0.95 * len(ordered)))
        ordered_tiles = sorted(tile_samples)
        return {"iterations": len(samples), "load_ms": {"min": min(samples), "p95": ordered[p95_index], "max": max(samples)},
                "tile_read_ms": {"min": min(tile_samples), "p95": ordered_tiles[p95_index], "max": max(tile_samples)},
                "peak_rss_proxy_bytes": max(peaks), "province_count": len(pack.ids["provinces"])}

    def _json(self, relative: str) -> Any:
        try:
            return json.loads((self.root / relative).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeLoadError(f"cannot read runtime asset {relative}: {exc}") from exc

    def _status_table(self, relative: str) -> tuple[tuple[int, ...], ...]:
        data = (self.root / relative).read_bytes()
        if data[:8] != b"GPMSTA1\0":
            raise RuntimeLoadError(f"invalid status table: {relative}")
        count, record_size = struct.unpack_from("<II", data, 8)
        if record_size != struct.calcsize("<BBHII") or len(data) != 16 + count * record_size:
            raise RuntimeLoadError(f"invalid status table size: {relative}")
        return tuple(struct.unpack_from("<BBHII", data, 16 + index * record_size) for index in range(count))

    def _status_delta(self, relative: str) -> tuple[set[tuple[int, ...]], set[tuple[int, ...]]]:
        data = (self.root / relative).read_bytes()
        if data[:8] != b"GPMDEL1\0":
            raise RuntimeLoadError(f"invalid status delta: {relative}")
        removed_count, added_count, record_size = struct.unpack_from("<III", data, 8)
        total = removed_count + added_count
        if record_size != struct.calcsize("<BBHII") or len(data) != 20 + total * record_size:
            raise RuntimeLoadError(f"invalid status delta size: {relative}")
        rows = [struct.unpack_from("<BBHII", data, 20 + index * record_size) for index in range(total)]
        return set(rows[:removed_count]), set(rows[removed_count:])
