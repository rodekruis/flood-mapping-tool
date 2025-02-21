import io
import json
import os
import zipfile
from pathlib import Path

import folium
import requests
from dotenv import load_dotenv

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


def download_gfm_geojson(
    area_name, from_date=None, to_date=None, output_file_path=None
):
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

    # Get Area of Impact
    aoi_url = f"{base_url}/aoi/user/{user_id}"
    response = requests.get(aoi_url, headers=header)

    # TODO: now only getting the first AOI, should extend to getting the whole list and unioning the geojsons
    for aoi in response.json()["aois"]:
        if aoi["aoi_name"] == area_name:
            aoi_id = aoi["aoi_id"]
            break

    # Get all product IDs
    params = {
        "time": "range",
        "from": f"{from_date}T00:00:00",
        "to": f"{to_date}T00:00:00",
    }
    prod_url = f"{base_url}/aoi/{aoi_id}/products"
    response = requests.get(prod_url, headers=header, params=params)
    products = response.json()["products"]
    print(f"Found {len(products)} products for {area_name}")

    if not output_file_path:
        base_file_path = "./output"

    # Download all available flood products
    for product in products:
        product_id = product["product_id"]

        # Converts product_time from e.g. "2025-01-05T06:10:37" to ""2025-01-05 06h
        # Reason for bucketing per hour is that products are often seconds or minutes apart and should be grouped
        product_time = product["product_time"]
        product_time = product_time.split(":")[0].replace("T", " ") + "h"
        output_file_path = f"{base_file_path}/{area_name}/{product_time}"
        Path(output_file_path).mkdir(parents=True, exist_ok=True)

        print(f"Downloading product: {product_id}")

        download_url = f"{base_url}/download/product/{product_id}"
        response = requests.get(download_url, headers=header)
        download_link = response.json()["download_link"]

        # Download and unzip file
        r = requests.get(download_link)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            print("Extracting...")
            z.extractall(str(Path(output_file_path)))

    print("Done!")


def retrieve_all_aois():
    print("Retrieving all AOIs from GFM API")
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

    aoi_url = f"{base_url}/aoi/user/{user_id}"
    response = requests.get(aoi_url, headers=header)

    aois = response.json()["aois"]

    return aois


def get_existing_flood_geojson(area_name, product_time, output_file_path=None):
    """
    Getting a saved GFM flood geojson in an output folder of GFM files. Merge in one feature group if multiple.
    """
    product_time = product_time.replace(":", "_")
    if not output_file_path:
        output_file_path = f"./output/{area_name}/{product_time}"

    # Combine multiple flood files into a FeatureGroup
    flood_geojson_group = folium.FeatureGroup(name=f"{area_name} Floods {product_time}")

    for flood_file in Path(output_file_path).glob("*FLOOD*.geojson"):
        with open(flood_file, "r") as f:
            geojson_data = json.load(f)
            flood_layer = folium.GeoJson(geojson_data)
            flood_geojson_group.add_child(flood_layer)

    # TODO: consider merging multiple flood layers into one, to avoid overlap

    return flood_geojson_group
