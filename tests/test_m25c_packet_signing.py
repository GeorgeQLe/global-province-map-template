"""Frozen M25C packet verification, signing, and downstream overlay flows."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "start-dates" / "1444-global-v1" / "census-research.json"


def _module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _packet(tmp_path: Path) -> Path:
    packet = tmp_path / "packet"
    _module("m25c_generator_test", "scripts/generate-m25c-anomaly-census.py").generate(
        RESEARCH,
        packet,
    )
    return packet


def _frozen_hashes(packet: Path) -> dict[str, str]:
    return {
        path.relative_to(packet).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in packet.rglob("*")
        if path.is_file() and path.name != "review_acceptance.json"
    }


def test_pending_sign_accepted_and_downstream_overlay_flow(tmp_path):
    verifier = _module("m25c_verifier_flow_test", "scripts/verify-m25c-anomaly-census.py")
    builder = _module("m25c_builder_flow_test", "scripts/build-m25c-global-pass.py")
    packet = _packet(tmp_path)
    pending = verifier._validate_packet(packet, state="pending")
    assert pending["status"] == "pass"
    assert pending["human_review_complete"] is False
    before = _frozen_hashes(packet)

    signed = verifier._sign(
        packet,
        reviewer="Ada Lovelace",
        review_date="2026-08-06",
    )
    assert signed["status"] == "signed"
    assert _frozen_hashes(packet) == before
    accepted = verifier._validate_packet(packet, state="accepted")
    assert accepted["reviewer"] == "Ada Lovelace"
    assert accepted["human_review_complete"] is True
    assert accepted["public_release_allowed"] is False

    overlay = builder._load_accepted_inventory(
        packet / "anomaly_inventory.json",
        packet / "review_acceptance.json",
    )
    assert overlay["census"]["reviewer"] == "Ada Lovelace"
    assert overlay["census"]["review_date"] == "2026-08-06"
    assert (packet / "anomaly_inventory.json").read_bytes()


@pytest.mark.parametrize(
    "reviewer,review_date,match",
    [
        ("OpenAI Codex (research agent)", "2026-08-06", "distinct named human"),
        ("Placeholder", "2026-08-06", "distinct named human"),
        ("Generator", "2026-08-06", "distinct named human"),
        ("Ada Lovelace", "2026-02-30", "valid YYYY-MM-DD"),
    ],
)
def test_sign_rejects_generator_placeholder_and_invalid_date(
    tmp_path, reviewer, review_date, match,
):
    verifier = _module(
        f"m25c_verifier_rejection_{reviewer}_{review_date}",
        "scripts/verify-m25c-anomaly-census.py",
    )
    with pytest.raises(SystemExit, match=match):
        verifier._sign(
            _packet(tmp_path),
            reviewer=reviewer,
            review_date=review_date,
        )


def test_sign_rejects_duplicate_sidecar(tmp_path):
    verifier = _module("m25c_verifier_duplicate_test", "scripts/verify-m25c-anomaly-census.py")
    packet = _packet(tmp_path)
    verifier._sign(packet, reviewer="Ada Lovelace", review_date="2026-08-06")
    with pytest.raises(SystemExit, match="duplicate signature"):
        verifier._sign(packet, reviewer="Grace Hopper", review_date="2026-08-06")


def test_sign_rejects_tampered_frozen_file(tmp_path):
    verifier = _module("m25c_verifier_tamper_test", "scripts/verify-m25c-anomaly-census.py")
    packet = _packet(tmp_path)
    path = packet / "dossier.md"
    path.write_text(path.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="hash verification failed"):
        verifier._sign(packet, reviewer="Ada Lovelace", review_date="2026-08-06")
