#!/usr/bin/env python3
"""Regenerate the deterministic M25B synthetic reference pack."""

import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gpm.runtime import compile_runtime_pack


OUTPUT = ROOT / "samples" / "m25b-runtime-reference"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    output = args.output_dir
    if output.exists():
        shutil.rmtree(output)
    compile_runtime_pack(
        ROOT / "tests" / "fixtures" / "m25a" / "casebook.json",
        output,
        pack_id="m25b-hard-cases-v1",
        compatibility_revision="1",
        include_debug_symbols=False,
        min_zoom=0,
        max_zoom=1,
    )


if __name__ == "__main__":
    main()
