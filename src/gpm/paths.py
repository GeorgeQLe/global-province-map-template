from __future__ import annotations

import os
import sysconfig
from pathlib import Path


PACKAGE_DATA_ROOT = Path(sysconfig.get_path("data")) / "share" / "global-province-map-template"


def _has_project_data(root: Path) -> bool:
    return (root / "configs").is_dir() and (root / "schemas").is_dir()


def _resolve_project_root() -> Path:
    env_root = os.environ.get("GPM_PROJECT_ROOT")
    candidates = [
        Path(env_root).expanduser() if env_root else None,
        Path(__file__).resolve().parents[2],
        Path.cwd(),
        PACKAGE_DATA_ROOT,
    ]
    for candidate in candidates:
        if candidate is not None and _has_project_data(candidate):
            return candidate
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _resolve_project_root()
CONFIG_DIR = PROJECT_ROOT / "configs"
PROFILE_DIR = CONFIG_DIR / "profiles"
SCHEMA_DIR = PROJECT_ROOT / "schemas"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERMEDIATE_DATA_DIR = DATA_DIR / "intermediate"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
