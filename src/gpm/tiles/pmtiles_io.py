"""PMTiles v3 archive writer and minimal reader.

Implements enough of the PMTiles v3 specification to write clustered MVT
archives and to read headers / individual tiles for tests and tooling.
See https://github.com/protomaps/PMTiles/blob/main/spec/v3/spec.md
"""

from __future__ import annotations

import gzip
import io
import json
import tempfile
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any


class Compression(IntEnum):
    UNKNOWN = 0
    NONE = 1
    GZIP = 2
    BROTLI = 3
    ZSTD = 4


class TileType(IntEnum):
    UNKNOWN = 0
    MVT = 1
    PNG = 2
    JPEG = 3
    WEBP = 4
    AVIF = 5


@dataclass
class DirectoryEntry:
    tile_id: int
    offset: int
    length: int
    run_length: int


def write_varint(buf: io.BytesIO, value: int) -> None:
    if value < 0:
        raise ValueError("varint must be non-negative")
    while True:
        bits = value & 0x7F
        value >>= 7
        if value:
            buf.write(bytes([bits | 0x80]))
        else:
            buf.write(bytes([bits]))
            break


def read_varint(buf: io.BytesIO) -> int:
    shift = 0
    result = 0
    while True:
        raw = buf.read(1)
        if raw == b"":
            raise EOFError("unexpected end of varint stream")
        byte = raw[0]
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return result


def rotate(n: int, x: int, y: int, rx: int, ry: int) -> tuple[int, int]:
    if ry == 0:
        if rx != 0:
            x = n - 1 - x
            y = n - 1 - y
        x, y = y, x
    return x, y


def zxy_to_tileid(z: int, x: int, y: int) -> int:
    if z > 31:
        raise OverflowError("tile zoom exceeds 64-bit limit")
    if x > (1 << z) - 1 or y > (1 << z) - 1:
        raise ValueError("tile x/y outside zoom level bounds")
    acc = ((1 << (z * 2)) - 1) // 3
    a = z - 1
    while a >= 0:
        s = 1 << a
        rx = s & x
        ry = s & y
        acc += ((3 * rx) ^ ry) << a
        x, y = rotate(s, x, y, rx, ry)
        a -= 1
    return acc


def tileid_to_zxy(tile_id: int) -> tuple[int, int, int]:
    z = ((3 * tile_id + 1).bit_length() - 1) // 2
    if z >= 32:
        raise OverflowError("tile zoom exceeds 64-bit limit")
    acc = ((1 << (z * 2)) - 1) // 3
    pos = tile_id - acc
    x = 0
    y = 0
    s = 1
    n = 1 << z
    while s < n:
        rx = (pos // 2) & s
        ry = (pos ^ rx) & s
        x, y = rotate(s, x, y, rx, ry)
        x += rx
        y += ry
        pos >>= 1
        s <<= 1
    return z, x, y


def serialize_directory(entries: list[DirectoryEntry]) -> bytes:
    buf = io.BytesIO()
    write_varint(buf, len(entries))
    last_id = 0
    for entry in entries:
        write_varint(buf, entry.tile_id - last_id)
        last_id = entry.tile_id
    for entry in entries:
        write_varint(buf, entry.run_length)
    for entry in entries:
        write_varint(buf, entry.length)
    for index, entry in enumerate(entries):
        if index > 0 and entry.offset == entries[index - 1].offset + entries[index - 1].length:
            write_varint(buf, 0)
        else:
            write_varint(buf, entry.offset + 1)
    return gzip.compress(buf.getvalue())


def deserialize_directory(data: bytes) -> list[DirectoryEntry]:
    buf = io.BytesIO(gzip.decompress(data))
    count = read_varint(buf)
    entries: list[DirectoryEntry] = []
    last_id = 0
    for _ in range(count):
        delta = read_varint(buf)
        last_id += delta
        entries.append(DirectoryEntry(last_id, 0, 0, 0))
    for entry in entries:
        entry.run_length = read_varint(buf)
    for entry in entries:
        entry.length = read_varint(buf)
    for index, entry in enumerate(entries):
        value = read_varint(buf)
        if index > 0 and value == 0:
            entry.offset = entries[index - 1].offset + entries[index - 1].length
        else:
            entry.offset = value - 1
    return entries


def _build_roots_leaves(
    entries: list[DirectoryEntry], leaf_size: int
) -> tuple[bytes, bytes, int]:
    root_entries: list[DirectoryEntry] = []
    leaves = bytearray()
    num_leaves = 0
    i = 0
    while i < len(entries):
        num_leaves += 1
        serialized = serialize_directory(entries[i : i + leaf_size])
        root_entries.append(
            DirectoryEntry(entries[i].tile_id, len(leaves), len(serialized), 0)
        )
        leaves.extend(serialized)
        i += leaf_size
    return serialize_directory(root_entries), bytes(leaves), num_leaves


def optimize_directories(
    entries: list[DirectoryEntry], target_root_len: int
) -> tuple[bytes, bytes, int]:
    test = serialize_directory(entries)
    if len(test) < target_root_len:
        return test, b"", 0
    leaf_size = 4096
    while True:
        root_bytes, leaves_bytes, num_leaves = _build_roots_leaves(entries, leaf_size)
        if len(root_bytes) < target_root_len:
            return root_bytes, leaves_bytes, num_leaves
        leaf_size *= 2


def serialize_header(header: dict[str, Any]) -> bytes:
    parts = bytearray()
    parts.extend(b"PMTiles")
    parts.append(3)

    def u64(value: int) -> None:
        parts.extend(int(value).to_bytes(8, "little", signed=False))

    def i32(value: int) -> None:
        parts.extend(int(value).to_bytes(4, "little", signed=True))

    def u8(value: int) -> None:
        parts.append(int(value) & 0xFF)

    u64(header["root_offset"])
    u64(header["root_length"])
    u64(header["metadata_offset"])
    u64(header["metadata_length"])
    u64(header.get("leaf_directory_offset", 0))
    u64(header.get("leaf_directory_length", 0))
    u64(header["tile_data_offset"])
    u64(header["tile_data_length"])
    u64(header.get("addressed_tiles_count", 0))
    u64(header.get("tile_entries_count", 0))
    u64(header.get("tile_contents_count", 0))
    parts.append(0x01 if header.get("clustered", True) else 0x00)
    u8(int(header.get("internal_compression", Compression.GZIP)))
    u8(int(header.get("tile_compression", Compression.GZIP)))
    u8(int(header.get("tile_type", TileType.MVT)))
    u8(header["min_zoom"])
    u8(header["max_zoom"])
    min_lon_e7 = header.get("min_lon_e7", int(-180 * 10_000_000))
    min_lat_e7 = header.get("min_lat_e7", int(-90 * 10_000_000))
    max_lon_e7 = header.get("max_lon_e7", int(180 * 10_000_000))
    max_lat_e7 = header.get("max_lat_e7", int(90 * 10_000_000))
    i32(min_lon_e7)
    i32(min_lat_e7)
    i32(max_lon_e7)
    i32(max_lat_e7)
    u8(header.get("center_zoom", header["min_zoom"]))
    i32(header.get("center_lon_e7", round((min_lon_e7 + max_lon_e7) / 2)))
    i32(header.get("center_lat_e7", round((min_lat_e7 + max_lat_e7) / 2)))
    assert len(parts) == 127, f"header must be 127 bytes, got {len(parts)}"
    return bytes(parts)


def deserialize_header(buf: bytes) -> dict[str, Any]:
    if len(buf) < 127:
        raise ValueError("PMTiles header too short")
    if buf[0:7] != b"PMTiles":
        raise ValueError("not a PMTiles archive (bad magic)")
    if buf[7] != 3:
        raise ValueError(f"unsupported PMTiles version: {buf[7]}")

    def u64(pos: int) -> int:
        return int.from_bytes(buf[pos : pos + 8], "little", signed=False)

    def i32(pos: int) -> int:
        return int.from_bytes(buf[pos : pos + 4], "little", signed=True)

    return {
        "version": buf[7],
        "root_offset": u64(8),
        "root_length": u64(16),
        "metadata_offset": u64(24),
        "metadata_length": u64(32),
        "leaf_directory_offset": u64(40),
        "leaf_directory_length": u64(48),
        "tile_data_offset": u64(56),
        "tile_data_length": u64(64),
        "addressed_tiles_count": u64(72),
        "tile_entries_count": u64(80),
        "tile_contents_count": u64(88),
        "clustered": buf[96] == 1,
        "internal_compression": Compression(buf[97]),
        "tile_compression": Compression(buf[98]),
        "tile_type": TileType(buf[99]),
        "min_zoom": buf[100],
        "max_zoom": buf[101],
        "min_lon_e7": i32(102),
        "min_lat_e7": i32(106),
        "max_lon_e7": i32(110),
        "max_lat_e7": i32(114),
        "center_zoom": buf[118],
        "center_lon_e7": i32(119),
        "center_lat_e7": i32(123),
    }


class PmtilesWriter:
    """Stream tiles into a PMTiles v3 archive."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[DirectoryEntry] = []
        self._hash_to_offset: dict[int, int] = {}
        self._tile_tmp = tempfile.TemporaryFile()
        self._offset = 0
        self._addressed = 0
        self._clustered = True

    def write_tile(self, tile_id: int, data: bytes) -> None:
        if self._entries and tile_id < self._entries[-1].tile_id:
            self._clustered = False
        digest = hash(data)
        if digest in self._hash_to_offset:
            found = self._hash_to_offset[digest]
            last = self._entries[-1]
            if tile_id == last.tile_id + last.run_length and last.offset == found:
                last.run_length += 1
            else:
                self._entries.append(DirectoryEntry(tile_id, found, len(data), 1))
        else:
            self._tile_tmp.write(data)
            self._entries.append(DirectoryEntry(tile_id, self._offset, len(data), 1))
            self._hash_to_offset[digest] = self._offset
            self._offset += len(data)
        self._addressed += 1

    def finalize(
        self,
        *,
        metadata: dict[str, Any],
        min_zoom: int,
        max_zoom: int,
        bounds: tuple[float, float, float, float],
        center: tuple[float, float] | None = None,
        center_zoom: int | None = None,
        tile_compression: Compression = Compression.GZIP,
        tile_type: TileType = TileType.MVT,
    ) -> dict[str, Any]:
        if not self._entries:
            raise ValueError("cannot finalize PMTiles archive with no tiles")

        self._entries.sort(key=lambda entry: entry.tile_id)
        west, south, east, north = bounds
        if center is None:
            center = ((west + east) / 2.0, (south + north) / 2.0)
        if center_zoom is None:
            center_zoom = min_zoom

        root_bytes, leaves_bytes, _num_leaves = optimize_directories(
            self._entries, 16384 - 127
        )
        compressed_metadata = gzip.compress(
            json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )

        header: dict[str, Any] = {
            "clustered": self._clustered,
            "internal_compression": Compression.GZIP,
            "tile_compression": tile_compression,
            "tile_type": tile_type,
            "min_zoom": min_zoom,
            "max_zoom": max_zoom,
            "min_lon_e7": int(round(west * 10_000_000)),
            "min_lat_e7": int(round(south * 10_000_000)),
            "max_lon_e7": int(round(east * 10_000_000)),
            "max_lat_e7": int(round(north * 10_000_000)),
            "center_zoom": center_zoom,
            "center_lon_e7": int(round(center[0] * 10_000_000)),
            "center_lat_e7": int(round(center[1] * 10_000_000)),
            "addressed_tiles_count": self._addressed,
            "tile_entries_count": len(self._entries),
            "tile_contents_count": len(self._hash_to_offset),
            "root_offset": 127,
            "root_length": len(root_bytes),
        }
        header["metadata_offset"] = header["root_offset"] + header["root_length"]
        header["metadata_length"] = len(compressed_metadata)
        header["leaf_directory_offset"] = (
            header["metadata_offset"] + header["metadata_length"]
        )
        header["leaf_directory_length"] = len(leaves_bytes)
        header["tile_data_offset"] = (
            header["leaf_directory_offset"] + header["leaf_directory_length"]
        )
        header["tile_data_length"] = self._offset

        with self.path.open("wb") as out:
            out.write(serialize_header(header))
            out.write(root_bytes)
            out.write(compressed_metadata)
            out.write(leaves_bytes)
            self._tile_tmp.seek(0)
            while True:
                chunk = self._tile_tmp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        self._tile_tmp.close()
        return header


def read_pmtiles_header(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    with path.open("rb") as handle:
        return deserialize_header(handle.read(127))


def _find_tile_entry(entries: list[DirectoryEntry], tile_id: int) -> DirectoryEntry | None:
    lo = 0
    hi = len(entries) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        entry = entries[mid]
        if tile_id < entry.tile_id:
            hi = mid - 1
        elif entry.run_length == 0:
            # leaf pointer — not expanded here beyond one level below
            if tile_id == entry.tile_id:
                return entry
            # continue search: leaves cover ranges starting at tile_id
            if tile_id > entry.tile_id:
                lo = mid + 1
            else:
                hi = mid - 1
        elif tile_id < entry.tile_id:
            hi = mid - 1
        elif tile_id >= entry.tile_id + entry.run_length:
            lo = mid + 1
        else:
            return entry
    # Check nearest lower entry for run coverage.
    if 0 <= hi < len(entries):
        entry = entries[hi]
        if entry.run_length > 0 and entry.tile_id <= tile_id < entry.tile_id + entry.run_length:
            return entry
        if entry.run_length == 0:
            return entry
    return None


def read_pmtiles_tile(path: Path | str, z: int, x: int, y: int) -> bytes | None:
    """Return decompressed tile bytes for z/x/y, or None if missing."""
    path = Path(path)
    with path.open("rb") as handle:
        header = deserialize_header(handle.read(127))
        handle.seek(header["root_offset"])
        root = deserialize_directory(handle.read(header["root_length"]))
        tile_id = zxy_to_tileid(z, x, y)
        entry = _find_tile_entry(root, tile_id)
        if entry is None:
            return None
        if entry.run_length == 0:
            # Leaf directory
            handle.seek(header["leaf_directory_offset"] + entry.offset)
            leaf = deserialize_directory(handle.read(entry.length))
            entry = _find_tile_entry(leaf, tile_id)
            if entry is None or entry.run_length == 0:
                return None
        handle.seek(header["tile_data_offset"] + entry.offset)
        raw = handle.read(entry.length)
    if header["tile_compression"] == Compression.GZIP:
        return gzip.decompress(raw)
    if header["tile_compression"] == Compression.NONE:
        return raw
    raise ValueError(f"unsupported tile compression: {header['tile_compression']}")


def read_pmtiles_metadata(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    with path.open("rb") as handle:
        header = deserialize_header(handle.read(127))
        handle.seek(header["metadata_offset"])
        raw = handle.read(header["metadata_length"])
    if header["internal_compression"] == Compression.GZIP:
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))
