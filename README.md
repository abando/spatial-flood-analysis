# Flood Impact Analysis Tool

This Python project identifies buildings affected by flooding across multiple states and multiple flood data sources. It combines raster-based flood data (GeoTIFF), KML state boundaries, and GeoJSON building footprints to determine which buildings fall within flood-affected areas, and obtains their ZIP+4 codes via the Geocodio API.

## Key Features

- **Multi-State Processing:** Automatically iterates over all state boundary files (KML) in the `stateoutline` directory.
- **Multi-Flood Data Processing:** Automatically iterates over all TIFF flood data files in the `floodmaps` directory.
- **State-TIFF Combinations:** For each combination of state boundary and flood TIFF:
  - Clips the flood raster to the state's boundary.
  - Extracts flooded areas.
  - Identifies buildings affected by those flooded areas.
  - Retrieves ZIP+4 codes for a subset of affected buildings.
- **Customized Outputs:** Each state and flood TIFF combination produces separate outputs (CSV and PNG), named accordingly.

## Prerequisites

- **Python 3.7+**
- Required libraries:
  - `geopandas`
  - `rasterio`
  - `numpy`
  - `shapely`
  - `matplotlib`
  - `geopy`
  - `pandas`
  - `requests`

Install the required libraries using:

```bash
pip install geopandas rasterio numpy shapely matplotlib geopy pandas requests
```

## Directory Structure

- `stateoutline/`: Contains KML files for each state (e.g., `NorthCarolina.kml`, `SouthCarolina.kml`).
- `buildingdata/`: Contains GeoJSON building footprint files (e.g., `NorthCarolina.geojson`, `SouthCarolina.geojson`). Names match the state KML files.
- `floodmaps/`: Contains multiple GeoTIFF flood files (e.g., `sept2018.tif`, `oct2018.tif`).

All outputs will be generated in the current working directory with filenames including both the state name and the TIF name.

## Input Files

- **Flood Data (GeoTIFF)**: One or more GeoTIFF raster files in `floodmaps/`.
- **State Boundaries (KML)**: One or more state boundary KML files in `stateoutline/`.
- **Building Footprints (GeoJSON)**: Corresponding building footprint GeoJSON files in `buildingdata/` with names matching the state names.

## Setup

1. Clone or download this repository.
2. Place your input files in the appropriate directories:
   - State KML files in `stateoutline/`
   - Building GeoJSON files in `buildingdata/`
   - Flood GeoTIFF files in `floodmaps/`
3. Obtain a Geocodio API Key for reverse geocoding and ZIP+4 code generation.  
4. Set `geocodio_api_key` in the script to your key.

## Usage

Run the script:

```bash
python geoanalysis.py
```

The script will:

1. Loop through each TIFF file in `floodmaps/`.
2. For each TIFF, loop through each KML file in `stateoutline/`.
3. For each state-TIFF combination, clip the raster, identify flooded areas, find affected buildings, and fetch ZIP+4 codes.

## Output Files

For each state and TIFF combination, the script produces:

- **Affected Buildings CSV:** `<StateName>_<TIFName>_affected_buildings.csv`
- **Flood Map Visualization (PNG):** `<StateName>_<TIFName>_flood_affected_buildings.png`

(Optional) A clipped TIFF `<StateName>_<TIFName>_clipped_flood_map.tif` may also be saved if desired.

## Workflow

1. **Load State Boundary Data:** The script reads each KML file for the state's boundary.
2. **Load Building Data:** Reads the state's building footprints from GeoJSON.
3. **Clip Flood Data:** Clips the flood raster for each TIFF to the state boundary.
4. **Extract Flood-Affected Areas:** Identifies polygons of flooded regions.
5. **Identify Flood-Affected Buildings:** Performs a spatial join to find buildings in flooded areas.
6. **Geocode Building Locations:** Uses Geocodio API to fetch ZIP+4 codes for a sample of affected buildings.
7. **Generate Outputs:** Saves a CSV and PNG visualization for each state-TIFF combination.

## Notes

- Ensure all input data have compatible CRSs. The script attempts to reproject automatically.
- If a state has no flooding for a particular TIFF or no affected buildings, no CSV/PNG will be produced for that combination.
- Adjust RateLimiter or the Geocodio API usage as needed to avoid hitting rate limits.

## Example

**Input:**

- Flood Data: `floodmaps/sept2018.tif`, `floodmaps/oct2018.tif`
- States: `stateoutline/NorthCarolina.kml`, `stateoutline/SouthCarolina.kml`
- Buildings: `buildingdata/NorthCarolina.geojson`, `buildingdata/SouthCarolina.geojson`

**Output:**

- `NorthCarolina_sept2018_affected_buildings.csv`
- `NorthCarolina_sept2018_flood_affected_buildings.png`
- `NorthCarolina_oct2018_affected_buildings.csv`
- `NorthCarolina_oct2018_flood_affected_buildings.png`
- `SouthCarolina_sept2018_affected_buildings.csv`
- `SouthCarolina_sept2018_flood_affected_buildings.png`
- `SouthCarolina_oct2018_affected_buildings.csv`
- `SouthCarolina_oct2018_flood_affected_buildings.png`

## Troubleshooting

- **CRS Issues:** Verify the source data CRS. Use `gdalinfo` or `ogrinfo` to inspect CRS.
- **API Errors:** Check the Geocodio API key and ensure you’re not exceeding rate limits.
- **Empty Results:** Confirm overlapping coverage between the flood, state, and building data.

## License

This project is licensed under the MIT License. Feel free to use, modify, and distribute it.
```
