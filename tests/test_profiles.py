import tomllib

from conftest import PROJECT_ROOT


PROFILE_DIR = PROJECT_ROOT / "configs" / "profiles"
EXPECTED_PROFILES = {
    "modern-small",
    "modern-detailed",
    "hoi-like",
    "victoria-like",
    "eu-like",
}


def test_generation_profiles_parse_and_match_expected_ids():
    profile_paths = sorted(PROFILE_DIR.glob("*.toml"))
    assert {path.stem for path in profile_paths} == EXPECTED_PROFILES

    for path in profile_paths:
        with path.open("rb") as file:
            profile = tomllib.load(file)

        assert profile["profile"]["id"] == path.stem
        assert profile["profile"]["map_mode"]
        assert profile["sources"]["default"] == ["natural_earth", "geoboundaries"]
        assert "openstreetmap" not in profile["sources"]["default"]
        assert "gadm" not in profile["sources"]["default"]
        assert "gadm" in profile["sources"]["excluded"]
        assert profile["generation"]["target_province_count"] > 0
        assert profile["qa"]["topology_required"] is True
