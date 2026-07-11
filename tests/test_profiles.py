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
        assert 0 <= profile["refinement"]["population_weight"] <= 1
        assert profile["refinement"]["min_area_sq_km"] >= 0
        assert profile["refinement"]["min_population"] >= 0
        assert profile["refinement"]["max_split_parts"] >= 1
        assert (
            profile["refinement"]["max_seed_candidates"]
            >= profile["refinement"]["max_split_parts"]
        )
        assert profile["qa"]["topology_required"] is True
        assert profile["qa"]["max_overlap_area_sq_km"] == 1.0
        assert profile["qa"]["max_gap_component_area_sq_km"] == 10.0
        assert profile["qa"]["min_shared_border_km"] == 0.01
        assert profile["export"]["layout"]
        assert profile["export"]["region_type"] in {
            "state",
            "region",
            "strategic_region",
            "superregion",
        }
        assert isinstance(profile["export"]["include_sea_zones"], bool)
        assert isinstance(profile["export"]["include_geometry"], bool)
        assert profile["export"]["definition_format"] in {"json", "csv"}
        assert profile["export"]["localization_language"]
