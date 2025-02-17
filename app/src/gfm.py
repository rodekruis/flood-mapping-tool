import io
import json
import os
import warnings
import zipfile
from pathlib import Path

import folium
import requests
from dotenv import load_dotenv
from shapely.geometry import MultiPolygon, shape
from shapely.ops import unary_union

load_dotenv()


class FloodGeoJsonError(Exception):
    """Custom exception for errors in fetching flood GeoJSON files."""

    pass


def sync_cached_data(bboxes_path="./bboxes/bboxes.json", output_dir="./output"):
    """
    Ensures that all areas in bboxes.json have a corresponding folder in ./output/.
    Removes any area entry from bboxes.json that does not have an output folder.
    """
    try:
        # Load existing bounding boxes
        with open(bboxes_path, "r") as f:
            bboxes = json.load(f)

        # Get a set of existing output folders
        existing_folders = {
            folder.name for folder in Path(output_dir).iterdir() if folder.is_dir()
        }

        # Remove entries from bboxes.json if the folder does not exist
        updated_bboxes = {
            area: data for area, data in bboxes.items() if area in existing_folders
        }

        # If changes were made, overwrite bboxes.json
        if len(updated_bboxes) != len(bboxes):
            with open(bboxes_path, "w") as f:
                json.dump(updated_bboxes, f, indent=4)
            print(f"Updated {bboxes_path}: Removed missing areas.")
        else:
            print("All areas have matching folders.")

    except FileNotFoundError:
        print(f"Error: {bboxes_path} not found.")
    except json.JSONDecodeError:
        print(f"Error: {bboxes_path} is not a valid JSON file.")


def download_gfm_geojson(area_name, bbox, new_coordinates=None, output_file_path=None):
    """
    Should provide an existing area name or a new area name with new_coordinates
    """
    username = os.environ["gfm_username"]
    password = os.environ["gfm_password"]
    base_url = "https://api.gfm.eodc.eu/v1"

    # Get token, setup header
    token_url = f"{base_url}/auth/login"

    payload = {"email": username, "password": password}

    response = requests.post(token_url, json=payload)
    user_id = response.json()["client_id"]
    access_token = response.json()["access_token"]
    header = {"Authorization": f"bearer {access_token}"}
    print("logged in")

    # Only if new coordinates are provided create the AOI in GFM
    if new_coordinates:
        # Create area of impact
        create_aoi_url = f"{base_url}/aoi/create"

        payload = {
            "aoi_name": area_name,
            "description": area_name,
            "user_id": user_id,
            "geoJSON": {"type": "Polygon", "coordinates": [new_coordinates]},
        }

        r = requests.post(url=create_aoi_url, json=payload, headers=header)
        print("Posted new AOI")

    # Get Area of Impact
    aoi_url = f"{base_url}/aoi/user/{user_id}"
    response = requests.get(aoi_url, headers=header)

    # TODO: now only getting the first AOI, should extend to getting the whole list and unioning the geojsons
    for aoi in response.json()["aois"]:
        if aoi["aoi_name"] == area_name:
            aoi_id = aoi["aoi_id"]
            break
    #         print(aoi)

    # # Collect all matching AOIs (same name)
    # matching_geometries = []
    # for aoi in response.json()["aois"]:
    #     if aoi["aoi_name"] == area_name:
    #         geojson_geometry = aoi["geoJSON"]["geometry"]
    #         matching_geometries.append(shape(geojson_geometry))

    # if not matching_geometries:
    #     raise ValueError(f"No AOIs found for area name: {area_name}")

    # # Merge all matching AOI geometries into a single unified polygon
    # merged_geometry = unary_union(matching_geometries)

    # # Handle MultiPolygon cases (if AOIs are disjointed)
    # if merged_geometry.geom_type == "MultiPolygon":
    #     merged_geometry = MultiPolygon([p for p in merged_geometry])

    # # Convert back to GeoJSON
    # merged_geojson = {
    #     "type": "Feature",
    #     "properties": {"aoi_name": area_name},
    #     "geometry": json.loads(json.dumps(merged_geometry.__geo_interface__)),
    # }

    # print(f"Merged {len(matching_geometries)} AOIs into one for '{area_name}'.")

    # return merged_geojson

    # Get product id
    prod_url = f"{base_url}/aoi/{aoi_id}/products"
    response = requests.get(prod_url, headers=header)
    product_id = response.json()["products"][0]["product_id"]
    print(f"got product_id {product_id}")

    # Get download link
    download_url = f"{base_url}/download/product/{product_id}"
    response = requests.get(download_url, headers=header)
    download_link = response.json()["download_link"]
    print("Got download link")

    # Set output file path and create directory if it doesn't exist
    if not output_file_path:
        output_file_path = f"./output/{area_name}"

    Path(output_file_path).mkdir(parents=True, exist_ok=True)

    # Download and unzip file
    for f in Path(output_file_path).glob("*"):
        f.unlink()
    print("Donwloading...")
    r = requests.get(download_link)
    print("Extracting zip...")
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall(str(Path(output_file_path)))
    print("Done!")


def get_existing_flood_geojson(area_name, date_range, output_file_path=None):
    """
    Getting a saved GFM flood geojson in an output folder of GFM files. Merge in one feature group if multiple.
    """

    if not output_file_path:
        output_file_path = f"./output/{area_name}/{date_range}"

    # Ensure the output directory exists
    # if not Path(output_file_path).exists():
    #     raise FloodGeoJsonError(f"Error: Output folder '{output_file_path}' does not exist.")

    # Combine multiple flood files into a FeatureGroup
    flood_geojson_group = folium.FeatureGroup(name=f"{area_name} Floods {date_range}")

    for flood_file in Path(output_file_path).glob("*FLOOD*.geojson"):
        with open(flood_file, "r") as f:
            geojson_data = json.load(f)
            flood_layer = folium.GeoJson(geojson_data)
            flood_geojson_group.add_child(flood_layer)

    # TODO: consider merging multiple flood layers into one, to avoid overlap

    return flood_geojson_group


if __name__ == "__main__":
    # download_gfm_geojson('Catania')
    gj = get_existing_flood_geojson("Albufera Floods")
    print(type(gj))
