import os
import glob
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
from shapely.geometry import shape, mapping
from rasterio.features import shapes
import matplotlib.pyplot as plt
import pandas as pd
import requests
from urllib.parse import urlencode
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Configuration
state_outline_dir = 'stateoutline'
building_data_dir = 'buildingdata'
flood_map_dir = 'floodmaps'
geocodio_api_key = "YOUR-API-KEY"

geolocator = Nominatim(user_agent="geoapi")
geocode = RateLimiter(geolocator.reverse, min_delay_seconds=3)

def process_state_and_tif(state_name, tif_path):
    # Derive building and kml paths
    kml_path = os.path.join(state_outline_dir, f"{state_name}.kml")
    building_path = os.path.join(building_data_dir, f"{state_name}.geojson")

    # Check if files exist
    if not os.path.exists(kml_path) or not os.path.exists(building_path):
        print(f"Missing files for {state_name}, skipping.")
        return

    # Load data
    boundary_gdf = gpd.read_file(kml_path, driver='KML')
    buildings = gpd.read_file(building_path)
    tif_name = os.path.splitext(os.path.basename(tif_path))[0]

    print(f"Processing {state_name} with {tif_name}...")

    # Clip the flood map to the state boundary
    with rasterio.open(tif_path) as flood_map:
        if boundary_gdf.crs != flood_map.crs:
            boundary_gdf = boundary_gdf.to_crs(flood_map.crs)
        
        boundary_geom = [mapping(boundary_gdf.geometry.union_all())]
        out_image, out_transform = mask(flood_map, boundary_geom, crop=True)
        out_meta = flood_map.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })

    # Save clipped raster if desired
    clipped_tif_path = f"{state_name}_{tif_name}_clipped_flood_map.tif"
    with rasterio.open(clipped_tif_path, 'w', **out_meta) as dest:
        dest.write(out_image)
    print(f"Clipped flood map for {state_name} using {tif_name}.")

    # Extract flood polygons
    with rasterio.open(clipped_tif_path) as clipped_flood_map:
        # We assume band 1 = flood_extent and band 5 = permanent_water (as per original logic)
        if clipped_flood_map.count < 5:
            print(f"{state_name}-{tif_name}: Flood map has fewer than 5 bands, can't proceed.")
            return

        flood_extent = clipped_flood_map.read(1)
        permanent_water = clipped_flood_map.read(5)
        affected_area = np.where((flood_extent == 1) & (permanent_water == 0), 1, 0).astype(np.uint8)

        affected_polygons = [
            shape(s)
            for s, v in shapes(affected_area, transform=clipped_flood_map.transform)
            if v == 1
        ]

        if not affected_polygons:
            print(f"No flooded areas found in {state_name} for {tif_name}.")
            return

        flood_gdf = gpd.GeoDataFrame(geometry=affected_polygons, crs=clipped_flood_map.crs)
    print(f"Flood polygons extracted for {state_name} with {tif_name}.")

    # Reproject buildings if needed
    if buildings.crs != flood_gdf.crs:
        buildings = buildings.to_crs(flood_gdf.crs)
    print(f"CRS aligned for {state_name} with {tif_name}.")

    # Find affected buildings
    affected_buildings = gpd.sjoin(buildings, flood_gdf, how='inner', predicate='intersects')
    if affected_buildings.empty:
        print(f"No affected buildings found in {state_name} for {tif_name}.")
        return
    print(f"Affected buildings found for {state_name} with {tif_name}.")

    # Fetch ZIP+4 codes for first 10 affected buildings
    projected_buildings = affected_buildings.to_crs(epsg=32617)
    projected_buildings['latitude'] = projected_buildings.geometry.centroid.to_crs(epsg=4326).y
    projected_buildings['longitude'] = projected_buildings.geometry.centroid.to_crs(epsg=4326).x
    projected_buildings['zipcode'] = None

    for idx in projected_buildings.head(10).index:
        latitude = projected_buildings.at[idx, 'latitude']
        longitude = projected_buildings.at[idx, 'longitude']

        params = urlencode({"q": f"{latitude},{longitude}", "fields": "zip4", "api_key": geocodio_api_key})
        url = f"https://api.geocod.io/v1.7/reverse?{params}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data['results']:
                zip_code = data['results'][0]['address_components'].get('zip')
                raw_fields = str(data['results'][0].get('fields', {}))
                zip4 = None
                if "'plus4': ['" in raw_fields:
                    start_idx = raw_fields.find("'plus4': ['") + len("'plus4': ['")
                    end_idx = raw_fields.find("']", start_idx)
                    zip4 = raw_fields[start_idx:end_idx]

                projected_buildings.at[idx, 'zipcode'] = f"{zip_code}-{zip4}" if zip4 else zip_code
        else:
            print(f"Error fetching ZIP+4 code for index {idx}: {response.status_code} - {response.text}")

    # Save CSV
    columns_to_include = ['latitude', 'longitude', 'zipcode']
    csv_path = f"{state_name}_{tif_name}_affected_buildings.csv"
    projected_buildings[columns_to_include].to_csv(csv_path, index=False)
    print(f"Saved affected buildings CSV for {state_name} with {tif_name}.")

    # Create map
    fig, ax = plt.subplots(figsize=(12, 12))
    boundary_gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=1)
    flood_gdf.plot(ax=ax, color='blue', alpha=0.5)
    affected_buildings.plot(ax=ax, color='red', alpha=0.7)
    plt.title(f"Flood-Affected Buildings in {state_name} ({tif_name})")
    png_path = f"{state_name}_{tif_name}_flood_affected_buildings.png"
    plt.savefig(png_path)
    plt.close(fig)
    print(f"Saved affected buildings map for {state_name} with {tif_name}.")

    print(f"Processing complete for {state_name} with {tif_name}.")

# Main loops: 
# 1) Iterate over all TIF files in floodmaps/ 
# 2) For each TIF, iterate over all KML files in stateoutline/

for tif_file in glob.glob(os.path.join(flood_map_dir, "*.tif")):
    tif_name = os.path.splitext(os.path.basename(tif_file))[0]
    print(f"Starting processing for all states with {tif_name}...")
    for kml_file in glob.glob(os.path.join(state_outline_dir, "*.kml")):
        state_name = os.path.splitext(os.path.basename(kml_file))[0].replace(' ', '')
        process_state_and_tif(state_name, tif_file)
    print(f"Completed processing for all states with {tif_name}.")
