from __future__ import annotations

from .base import AdapterDescription, BaseSourceAdapter, PlannedDownload, PlannedLayer, SourceDefinition


_PLANNED_LAYERS = (
    PlannedLayer("land", "Land polygons and land mask candidates."),
    PlannedLayer("coastline", "Coastline reference geometry."),
    PlannedLayer("admin0_countries", "Admin-0 country boundaries."),
    PlannedLayer("admin1_states_provinces", "Admin-1 state/province boundaries."),
    PlannedLayer("rivers_lakes", "Rivers and lakes for visual and split hints."),
)


class NaturalEarthAdapter(BaseSourceAdapter):
    planned_layers = _PLANNED_LAYERS

    def planned_downloads(self) -> tuple[PlannedDownload, ...]:
        return (
            self._download(
                "land",
                "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip",
                "data/raw/natural_earth/ne_10m_land.zip",
            ),
            self._download(
                "coastline",
                "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_coastline.zip",
                "data/raw/natural_earth/ne_10m_coastline.zip",
            ),
            self._download(
                "admin0_countries",
                "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip",
                "data/raw/natural_earth/ne_10m_admin_0_countries.zip",
            ),
            self._download(
                "admin1_states_provinces",
                "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_1_states_provinces.zip",
                "data/raw/natural_earth/ne_10m_admin_1_states_provinces.zip",
            ),
            self._download(
                "rivers_lakes",
                "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_rivers_lake_centerlines.zip",
                "data/raw/natural_earth/ne_10m_rivers_lake_centerlines.zip",
            ),
        )


def create_adapter(definition: SourceDefinition) -> NaturalEarthAdapter:
    return NaturalEarthAdapter(definition)


def describe() -> AdapterDescription:
    return AdapterDescription(
        source_id="natural_earth",
        display_name="Natural Earth",
        planned_layers=_PLANNED_LAYERS,
    )
