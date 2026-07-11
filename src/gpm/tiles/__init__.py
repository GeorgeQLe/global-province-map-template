"""Pure-Python vector tile + PMTiles packaging (M19).

Generates Mapbox Vector Tiles (MVT) from GeoJSON and packs them into a
single-file PMTiles archive without requiring tippecanoe. An optional
tippecanoe backend is available when the binary is on PATH.
"""

from .build import (
    TileBuildError,
    TileBuildResult,
    build_pmtiles_from_features,
    build_pmtiles_from_geojson,
    export_tiles_from_atlas,
    export_tiles_pack,
)
from .pmtiles_io import read_pmtiles_header, read_pmtiles_tile

__all__ = [
    "TileBuildError",
    "TileBuildResult",
    "build_pmtiles_from_features",
    "build_pmtiles_from_geojson",
    "export_tiles_from_atlas",
    "export_tiles_pack",
    "read_pmtiles_header",
    "read_pmtiles_tile",
]
