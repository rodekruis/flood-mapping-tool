import io
import json
import os
import zipfile
from pathlib import Path

import folium
import requests
from dotenv import load_dotenv

load_dotenv()


def download_gfm_geojson(area_name, new_coordinates=None, output_file_path=None):
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
    r = requests.get(download_link)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall(str(Path(output_file_path)))


def get_existing_flood_geojson(area_name, output_file_path=None):
    """
    Getting a saved GFM flood geojson in an output folder of GFM files
    """
    if not output_file_path:
        output_file_path = f"./output/{area_name}"

    for f in Path(output_file_path).glob("*"):
        if "FLOOD" in str(f) and "geojson" in str(f):
            geojson_path = f
            break

    flood_geojson = folium.GeoJson(json.load(open(geojson_path)))
    return flood_geojson
