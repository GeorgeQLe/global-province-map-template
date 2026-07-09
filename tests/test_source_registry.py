import pytest

from gpm.config import list_profile_ids
from gpm.sources.registry import RestrictedSourceError, resolve_source_adapters


def test_adapter_registry_resolves_default_profile_sources():
    adapters = resolve_source_adapters("modern-small")

    assert [adapter.source_id for adapter in adapters] == ["natural_earth", "geoboundaries"]
    assert [adapter.display_name for adapter in adapters] == ["Natural Earth", "geoBoundaries"]


def test_default_profile_plans_exclude_osm_and_gadm():
    for profile_id in list_profile_ids():
        adapters = resolve_source_adapters(profile_id)
        source_ids = {adapter.source_id for adapter in adapters}

        assert "openstreetmap" not in source_ids
        assert "gadm" not in source_ids


def test_registry_rejects_restricted_gadm():
    with pytest.raises(RestrictedSourceError, match="restricted"):
        resolve_source_adapters("modern-small", ["gadm"])
