import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
from shapely.geometry import mapping, shape
from rasterio.features import shapes
import json
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import requests 
import pandas as pd
from urllib.parse import urlencode


geolocator = Nominatim(user_agent="geoapi")
geocode = RateLimiter(geolocator.reverse, min_delay_seconds=3)

# Step 1
nc_boundary = gpd.read_file('YOUR STATE KML', driver='KML')

print("Step 1 Complete")

# Step 2
buildings = gpd.read_file('YOUR STATE GEOJSON')

print("Step 2 Complete")


# Step 3
with rasterio.open('YOUR-TIF-FILE') as flood_map:
    if nc_boundary.crs != flood_map.crs:
        nc_boundary = nc_boundary.to_crs(flood_map.crs)
    
    nc_geom = [mapping(nc_boundary.geometry.union_all())]
    
    out_image, out_transform = mask(flood_map, nc_geom, crop=True)
    out_meta = flood_map.meta.copy()
    
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })
    
    with rasterio.open('clipped_flood_map.tif', 'w', **out_meta) as dest:
        dest.write(out_image)

print("Step 3 Complete")


# Step 4
with rasterio.open('clipped_flood_map.tif') as clipped_flood_map:
    flood_extent = clipped_flood_map.read(1)
    permanent_water = clipped_flood_map.read(5)

    affected_area = np.where((flood_extent == 1) & (permanent_water == 0), 1, 0).astype(np.uint8)

    affected_polygons = [
        shape(s)
        for s, v in shapes(affected_area, transform=clipped_flood_map.transform)
        if v == 1
    ]
    flood_gdf = gpd.GeoDataFrame(geometry=affected_polygons, crs=clipped_flood_map.crs)

print("Step 4 Complete")


# Step 5
if buildings.crs != flood_gdf.crs:
    buildings = buildings.to_crs(flood_gdf.crs)

print("Step 5 Complete")


# Step 6
affected_buildings = gpd.sjoin(buildings, flood_gdf, how='inner', predicate='intersects')

print("Step 6 Complete")

import requests

# Replace Nominatim setup with your Geocodio API key
geocodio_api_key = "YOUR-KEY" 

# Step 7
# Convert to EPSG:32617 for coordinates
projected_buildings = affected_buildings.to_crs(epsg=32617)

# Get latitude and longitude from building centroids
projected_buildings['latitude'] = projected_buildings.geometry.centroid.to_crs(epsg=4326).y
projected_buildings['longitude'] = projected_buildings.geometry.centroid.to_crs(epsg=4326).x

# Initialize ZIP+4 code column
projected_buildings['zipcode'] = None

# Fetch ZIP+4 codes for the first 10 rows using Geocodio
for idx in projected_buildings.head(10).index:
    latitude = projected_buildings.at[idx, 'latitude']
    longitude = projected_buildings.at[idx, 'longitude']
    
    # URL encode latitude and longitude values
    params = urlencode({"q": f"{latitude},{longitude}", "fields": "zip4", "api_key": geocodio_api_key})
    url = f"https://api.geocod.io/v1.7/reverse?{params}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            # Convert the raw response to string and extract zip and zip4
            zip_code = data['results'][0]['address_components'].get('zip')
            
            # Raw extraction for the full output
            raw_fields = str(data['results'][0].get('fields', {}))
            
            # Extract the 'plus4' value from the raw fields using a text-search approach
            if "'plus4': ['" in raw_fields:
                start_idx = raw_fields.find("'plus4': ['") + len("'plus4': ['")
                end_idx = raw_fields.find("']", start_idx)
                zip4 = raw_fields[start_idx:end_idx]
            else:
                zip4 = None
            
            # Format the ZIP+4 correctly
            projected_buildings.at[idx, 'zipcode'] = f"{zip_code}-{zip4}" if zip4 else zip_code
    else:
        print(f"Error fetching ZIP+4 code for index {idx}: {response.status_code} - {response.text}")




# Define columns to include in the output CSV
columns_to_include = ['latitude', 'longitude', 'zipcode', 'capture_dates_range', 'release']  # Add 'building_id' if available

# Save to CSV
projected_buildings[columns_to_include].to_csv('affected_buildings.csv', index=False)
print("Step 7 Complete")


# Step 8:

fig, ax = plt.subplots(figsize=(12, 12))
nc_boundary.plot(ax=ax, color='none', edgecolor='black', linewidth=1)
flood_gdf.plot(ax=ax, color='blue', alpha=0.5)
affected_buildings.plot(ax=ax, color='red', alpha=0.7)
plt.title("Flood-Affected Buildings in North Carolina")
plt.savefig('flood_affected_buildings.png')


print("Analysis complete. Affected buildings saved to 'affected_buildings.geojson', 'affected_buildings.csv', and 'flood_affected_buildings.png'.")


