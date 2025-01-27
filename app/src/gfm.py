import io
import json
import os
import zipfile
from pathlib import Path

import folium
import requests
from dotenv import load_dotenv
from streamlit_folium import st_folium

load_dotenv()


def download_stuff(coordinates):
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

    # Create area of impact
    create_aoi_url = f"{base_url}/aoi/create"

    payload = {
        "aoi_name": "new_area",
        "description": "new_area",
        "user_id": user_id,
        "geoJSON": {"type": "Polygon", "coordinates": [coordinates]},
    }

    r = requests.post(url=create_aoi_url, json=payload, headers=header)
    print(r.text)
    print("Posted new AOI")
    # Get Area of Impact
    aoi_url = f"{base_url}/aoi/user/{user_id}"

    response = requests.get(aoi_url, headers=header)
    for aoi in response.json()["aois"]:
        if aoi["aoi_name"] == "new_area":
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

    # Download and unzip file
    for f in Path("./output").glob("*"):
        f.unlink()
    r = requests.get(download_link)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("./output")


def visualise_stuff():
    # get geosjon with floods
    for f in Path("./output").glob("*"):
        if "FLOOD" in str(f) and "geojson" in str(f):
            geojson_path = f

    # Create map
    flood_geojson = json.load(open(geojson_path))

    m = folium.Map([54, -2], zoom_start=7)
    folium.GeoJson(flood_geojson, name="geojson").add_to(m)
    m
    st_folium(m, width=800, height=450, returned_objects=[])
