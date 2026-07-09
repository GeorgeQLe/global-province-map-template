from __future__ import annotations

from .base import AdapterDescription, BaseSourceAdapter, PlannedDownload, PlannedLayer, SourceDefinition


_PLANNED_LAYERS = (
    PlannedLayer("adm0", "Country-level administrative boundaries."),
    PlannedLayer("adm1", "First-order administrative boundaries."),
    PlannedLayer("adm2_plus", "Deeper administrative levels where reliable."),
)


class GeoBoundariesAdapter(BaseSourceAdapter):
    planned_layers = _PLANNED_LAYERS

    def planned_downloads(self) -> tuple[PlannedDownload, ...]:
        return (
            self._download(
                "adm0",
                "https://www.geoboundaries.org/api/current/gbOpen/ALL/ADM0/",
                "data/raw/geoboundaries/gbopen_all_adm0_api.json",
            ),
            self._download(
                "adm1",
                "https://www.geoboundaries.org/api/current/gbOpen/ALL/ADM1/",
                "data/raw/geoboundaries/gbopen_all_adm1_api.json",
            ),
            self._download(
                "adm2_plus",
                "https://www.geoboundaries.org/api/current/gbOpen/ALL/ADM2/",
                "data/raw/geoboundaries/gbopen_all_adm2_api.json",
            ),
            self._download(
                "adm2_plus",
                "https://www.geoboundaries.org/api/current/gbOpen/ALL/ADM3/",
                "data/raw/geoboundaries/gbopen_all_adm3_api.json",
            ),
            self._download(
                "adm2_plus",
                "https://www.geoboundaries.org/api/current/gbOpen/ALL/ADM4/",
                "data/raw/geoboundaries/gbopen_all_adm4_api.json",
            ),
            self._download(
                "adm2_plus",
                "https://www.geoboundaries.org/api/current/gbOpen/ALL/ADM5/",
                "data/raw/geoboundaries/gbopen_all_adm5_api.json",
            ),
        )


def create_adapter(definition: SourceDefinition) -> GeoBoundariesAdapter:
    return GeoBoundariesAdapter(definition)


def describe() -> AdapterDescription:
    return AdapterDescription(
        source_id="geoboundaries",
        display_name="geoBoundaries",
        planned_layers=_PLANNED_LAYERS,
    )
