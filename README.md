
# Flood Impact Analysis Tool

This Python project identifies buildings affected by flooding in a specific region by combining flood data, state boundaries, and building footprints. It supports any GeoTIFF flood data, KML state boundaries, and GeoJSON building data.

## Prerequisites

Ensure you have the following software and libraries installed:

-   Python 3.7+
-   Libraries:
    -   `geopandas`
    -   `rasterio`
    -   `numpy`
    -   `shapely`
    -   `matplotlib`
    -   `geopy`
    -   `pandas`
    -   `requests`

Install the required libraries using `pip`:

bash

Copy code

`pip install geopandas rasterio numpy shapely matplotlib geopy pandas requests` 

## Input Files

To use this script, provide the following input files:

### Flood Data (GeoTIFF):

Geo-referenced raster file containing flood information.

### State Boundary Data (KML):

A KML file representing the state boundaries for analysis.

### Building Footprints (GeoJSON):

A GeoJSON file with building footprint geometries.

## Setup

1.  Clone or download this repository.
2.  Place your input files in the same directory as the script.
3.  Obtain a Geocodio API Key for reverse geocoding and ZIP+4 code generation.

## Configuration

Update the script with your file names and API key:

-   Replace `North Carolina.kml` with your state boundary KML file.
-   Replace `NorthCarolina.geojson` with your building footprint GeoJSON file.
-   Replace `DFO_4676_From_20180915_to_20181002.tif` with your flood data GeoTIFF file.
-   Replace `geocodio_api_key` in the script with your Geocodio API key.

## Usage

Run the script:

bash

Copy code

`python flood_analysis.py` 

## Output Files

### Clipped Flood Map (`clipped_flood_map.tif`):

A GeoTIFF file showing the flood data clipped to the state boundary.

### Flood-Affected Buildings (`affected_buildings.csv`):

A CSV file listing latitude, longitude, ZIP+4 codes, and additional data for buildings affected by flooding.

### Flood-Affected Buildings Visualization (`flood_affected_buildings.png`):

A visual map showing flood-affected areas and buildings.

## Workflow

1.  **Load State Boundary Data**: The script reads the KML file to extract the state boundary.
2.  **Load Building Data**: The GeoJSON file containing building footprints is loaded and prepared for spatial operations.
3.  **Clip Flood Data**: The flood GeoTIFF file is clipped to the state boundary.
4.  **Extract Flood-Affected Areas**: The clipped flood data is analyzed to identify areas affected by flooding.
5.  **Identify Flood-Affected Buildings**: A spatial join is performed between flood-affected areas and building footprints to identify impacted buildings.
6.  **Geocode Building Locations**: The Geocodio API is used to fetch ZIP+4 codes for the centroids of affected buildings.
7.  **Generate Outputs**: The script saves results to a CSV file, GeoJSON file, and visualization.

## Notes

-   Ensure all input files are in the correct geospatial formats and have valid coordinate reference systems (CRS).
-   The script includes automatic CRS alignment for the input files.
-   Adjust the Geocodio API request delay (RateLimiter) if rate limits are exceeded.

## Example

**Input:**

-   Flood Data: `sample_flood.tif`
-   State Boundary: `sample_state.kml`
-   Building Footprints: `sample_buildings.geojson`

**Output:**

-   `clipped_flood_map.tif`
-   `affected_buildings.csv`
-   `flood_affected_buildings.png`

## Troubleshooting

-   **CRS Mismatch**: Ensure all input files have valid CRS and are correctly aligned.
-   **API Errors**: Check your Geocodio API key and ensure you don’t exceed the request limits.
-   **Missing Data**: Verify the completeness of your input files and ensure they cover the same geographical region.

## License

This project is licensed under the MIT License. Feel free to use and modify it.
