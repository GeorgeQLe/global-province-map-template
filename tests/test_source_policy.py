import tomllib

from conftest import PROJECT_ROOT


def load_sources():
    with (PROJECT_ROOT / "configs" / "sources.toml").open("rb") as file:
        return tomllib.load(file)["sources"]


def test_restricted_gadm_is_not_enabled_by_default():
    gadm = load_sources()["gadm"]

    assert gadm["restricted"] is True
    assert gadm["enabled_by_default"] is False
    assert gadm["eligible_for_default_build"] is False
    assert gadm["default_path"] == "excluded"


def test_osm_is_optional_and_isolated():
    osm = load_sources()["openstreetmap"]

    assert osm["license"] == "ODbL"
    assert osm["optional"] is True
    assert osm["isolated"] is True
    assert osm["enabled_by_default"] is False
    assert osm["eligible_for_default_build"] is False
    assert osm["default_path"] == "optional-isolated"
