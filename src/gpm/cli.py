from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .config import DEFAULT_PROFILE_ID, ConfigError, load_profile
from .manifest import (
    build_downloaded_source_manifest,
    build_local_source_manifest,
    build_planned_source_manifest,
)
from .paths import RAW_DATA_DIR
from .schemas import validate_source_manifest
from .sources.artifacts import SourceArtifactError, download_source_artifacts
from .sources.registry import SourceRegistryError, resolve_source_adapters


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2
    return args.handler(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gpm",
        description="Generate EU/Victoria/HOI-style global province maps from open geodata.",
    )
    subcommands = parser.add_subparsers(dest="group")

    sources = subcommands.add_parser("sources", help="Manage source downloads and manifests.")
    source_commands = sources.add_subparsers(dest="command")
    download = source_commands.add_parser("download", help="Download or plan source artifacts.")
    _add_profile_arg(download)
    _add_source_arg(download)
    _add_raw_dir_arg(download)
    download.add_argument(
        "--execute",
        action="store_true",
        help="Fetch source artifacts. Omit for a dry-run plan.",
    )
    download.add_argument(
        "--force",
        action="store_true",
        help="Re-download artifacts even when target files already exist.",
    )
    download.add_argument(
        "--manifest-output",
        type=Path,
        help="Path for the downloaded source manifest. Defaults to <raw-dir>/source_manifest.json.",
    )
    download.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds when --execute is used. Defaults to 60.",
    )
    download.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format. Dry runs emit planned records; executed downloads emit the manifest.",
    )
    download.set_defaults(handler=_sources_download)
    manifest = source_commands.add_parser("manifest", help="Print a planned source manifest.")
    _add_profile_arg(manifest)
    _add_source_arg(manifest)
    _add_raw_dir_arg(manifest)
    manifest.add_argument(
        "--from-raw",
        action="store_true",
        help="Hash local raw artifacts and emit a downloaded/build manifest instead of a planned manifest.",
    )
    manifest.add_argument(
        "--output",
        type=Path,
        help="Optional path for writing the planned manifest JSON. Defaults to stdout only.",
    )
    manifest.set_defaults(handler=_sources_manifest)

    build = subcommands.add_parser("build", help="Build generated map layers.")
    build_commands = build.add_subparsers(dest="command")
    provinces = build_commands.add_parser("provinces", help="Placeholder for province generation.")
    _add_profile_arg(provinces)
    provinces.set_defaults(handler=_build_provinces)
    adjacency = build_commands.add_parser("adjacency", help="Placeholder for adjacency generation.")
    _add_profile_arg(adjacency)
    adjacency.set_defaults(handler=_build_adjacency)

    export = subcommands.add_parser("export", help="Export generated outputs.")
    export_commands = export.add_subparsers(dest="command")
    geojson = export_commands.add_parser("geojson", help="Placeholder for GeoJSON export.")
    _add_profile_arg(geojson)
    geojson.set_defaults(handler=_export_geojson)

    qa = subcommands.add_parser("qa", help="Run quality checks and review outputs.")
    qa_commands = qa.add_subparsers(dest="command")
    topology = qa_commands.add_parser("topology", help="Placeholder for topology QA.")
    _add_profile_arg(topology)
    topology.set_defaults(handler=_qa_topology)
    render = qa_commands.add_parser("render", help="Placeholder for visual render QA.")
    _add_profile_arg(render)
    render.set_defaults(handler=_qa_render)

    return parser


def _add_profile_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE_ID,
        help=f"Generation profile id. Defaults to {DEFAULT_PROFILE_ID}.",
    )


def _add_source_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="Source id to plan. May be provided more than once. Defaults to profile sources.default.",
    )


def _add_raw_dir_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help=f"Directory for raw source artifacts. Defaults to {RAW_DATA_DIR}.",
    )


def _sources_download(args: argparse.Namespace) -> int:
    try:
        adapters = resolve_source_adapters(args.profile, args.sources)
    except (ConfigError, SourceRegistryError) as error:
        _print_error(error)
        return 1

    if args.execute:
        try:
            artifacts_by_source = download_source_artifacts(
                adapters,
                raw_dir=args.raw_dir,
                force=args.force,
                timeout=args.timeout,
            )
            manifest = build_downloaded_source_manifest(args.profile, adapters, artifacts_by_source)
            validate_source_manifest(manifest)
        except SourceArtifactError as error:
            _print_error(error)
            return 1

        manifest_output = args.manifest_output or args.raw_dir / "source_manifest.json"
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.format == "json":
            print(json.dumps(manifest, indent=2, sort_keys=True))
            return 0

        artifact_count = sum(len(artifacts) for artifacts in artifacts_by_source.values())
        print("gpm sources download: downloaded or verified source artifacts.")
        print(f"Profile: {args.profile}")
        print(f"Raw data dir: {args.raw_dir}")
        print(f"Manifest: {manifest_output}")
        print(f"Artifact records: {artifact_count}")
        for artifacts in artifacts_by_source.values():
            for artifact in artifacts:
                print(f"- {artifact.source_id}/{artifact.layer_id}/{artifact.artifact_id}")
                print(f"  Status: {artifact.status}")
                print(f"  Path: {artifact.path}")
                print(f"  Bytes: {artifact.bytes}")
                print(f"  Checksum: {artifact.checksum}")
        return 0

    records = [record for adapter in adapters for record in adapter.planned_downloads()]
    if args.format == "json":
        print(json.dumps([record.to_dict() for record in records], indent=2, sort_keys=True))
        return 0

    print("gpm sources download: dry run only; no datasets were downloaded.")
    print(f"Profile: {args.profile}")
    print(f"Source plan: {', '.join(f'{adapter.display_name} ({adapter.source_id})' for adapter in adapters)}")
    print(f"Planned records: {len(records)}")
    for record in records:
        print(f"- {record.source_id}/{record.layer_id}")
        print(f"  URL: {record.url}")
        print(f"  Expected path: {record.expected_path}")
        print(f"  License: {record.license}")
        print(
            "  Policy: "
            f"default={record.default}, "
            f"optional={record.optional}, "
            f"isolated={record.isolated}, "
            f"restricted={record.restricted}"
        )
    return 0


def _sources_manifest(args: argparse.Namespace) -> int:
    try:
        if args.from_raw:
            manifest = build_local_source_manifest(args.profile, args.sources, raw_dir=args.raw_dir)
        else:
            manifest = build_planned_source_manifest(args.profile, args.sources)
        validate_source_manifest(manifest)
    except (ConfigError, SourceRegistryError, SourceArtifactError) as error:
        _print_error(error)
        return 1

    encoded = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(encoded, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        print(f"Wrote source manifest: {args.output}")
    return 0


def _build_provinces(args: argparse.Namespace) -> int:
    profile = _load_profile_or_report(args.profile)
    if profile is None:
        return 1
    target = profile["generation"]["target_province_count"]
    print("gpm build provinces: Phase 1 placeholder; no province geometry was generated.")
    print(f"Profile: {args.profile}; target province count: {target}")
    print("Future output: data/processed/provinces.geojson or data/processed/provinces.fgb")
    return 0


def _build_adjacency(args: argparse.Namespace) -> int:
    if _load_profile_or_report(args.profile) is None:
        return 1
    print("gpm build adjacency: Phase 1 placeholder; no adjacency table was generated.")
    print(f"Profile: {args.profile}")
    print("Future output: data/processed/adjacency.csv")
    return 0


def _export_geojson(args: argparse.Namespace) -> int:
    if _load_profile_or_report(args.profile) is None:
        return 1
    print("gpm export geojson: Phase 1 placeholder; no export files were written.")
    print(f"Profile: {args.profile}")
    print("Future output: exports/geojson/")
    return 0


def _qa_topology(args: argparse.Namespace) -> int:
    if _load_profile_or_report(args.profile) is None:
        return 1
    print("gpm qa topology: Phase 1 placeholder; topology checks are not implemented yet.")
    print(f"Profile: {args.profile}")
    print("Future checks: valid geometry, gaps, overlaps, orphan provinces, missing parents.")
    return 0


def _qa_render(args: argparse.Namespace) -> int:
    if _load_profile_or_report(args.profile) is None:
        return 1
    print("gpm qa render: Phase 1 placeholder; render snapshots are not implemented yet.")
    print(f"Profile: {args.profile}")
    print("Future review: static map images and optional MapLibre viewer snapshots.")
    return 0


def _load_profile_or_report(profile_id: str) -> dict | None:
    try:
        return load_profile(profile_id)
    except ConfigError as error:
        _print_error(error)
        return None


def _print_error(error: Exception) -> None:
    print(f"error: {error}", file=sys.stderr)
