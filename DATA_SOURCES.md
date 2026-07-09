# Data Sources

This project should keep data source decisions explicit and auditable. The table below is the starting policy, not a substitute for legal review.

| Source | Suggested Use | License Posture | Default Build |
| --- | --- | --- | --- |
| Natural Earth | Land, coastline, countries, rivers, lakes, basemap layers | Public domain | Yes |
| geoBoundaries | Administrative boundary candidates | CC BY 4.0, attribution required | Yes |
| GHSL | Built-up areas, population, settlement intensity | Open/free Copernicus/JRC data | Yes, after citation requirements are documented |
| WorldPop | Population count/density rasters | CC BY 4.0, attribution required | Yes |
| OpenHistoricalMap | Historical boundary and place hints | Mostly CC0, with per-feature exceptions | Optional |
| OpenStreetMap | Roads, settlements, ports, POIs, detailed geography | ODbL, attribution and share-alike obligations | Optional, isolated |
| GADM | Administrative boundaries | Non-commercial/academic; redistribution and commercial use restricted | No |

## Required Source Metadata

Every ingested layer should record:

- source name
- source URL
- access date
- version or release date
- original format
- checksum
- license
- attribution text
- transformation steps
- downstream files generated from the source

## Default Policy

- Do not commit raw downloaded datasets to git.
- Do not mix ODbL-derived data into permissive default builds.
- Do not use restricted data in published template outputs.
- Keep attribution machine-readable so exports can include the correct notices.
