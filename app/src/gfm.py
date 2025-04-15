import io
import os
import zipfile
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from src import hf_utils

load_dotenv()


@st.cache_resource
def get_gfm_user_and_token():
    username = os.environ["gfm_username"]
    password = os.environ["gfm_password"]
    base_url = "https://api.gfm.eodc.eu/v1"

    # Get token, setup header
    token_url = f"{base_url}/auth/login"

    payload = {"email": username, "password": password}

    response = requests.post(token_url, json=payload)
    user_id = response.json()["client_id"]
    access_token = response.json()["access_token"]
    print("retrieved user id and access token")

    return user_id, access_token


# Gets all products for an AOI in a daterange
def get_area_products(area_id, from_date, to_date):
    user_id, access_token = get_gfm_user_and_token()
    header = {"Authorization": f"bearer {access_token}"}

    base_url = "https://api.gfm.eodc.eu/v1"

    params = {
        "time": "range",
        "from": f"{from_date}T00:00:00",
        "to": f"{to_date}T00:00:00",
    }
    prod_url = f"{base_url}/aoi/{area_id}/products"
    response = requests.get(prod_url, headers=header, params=params)
    products = response.json()["products"]
    print(f"Found {len(products)} products for {area_id}")

    return products


# Will download a product by product_id, saves the flood geojson and updates the index for caching
def download_flood_product(area_id, product, output_file_path=None):
    user_id, access_token = get_gfm_user_and_token()
    header = {"Authorization": f"bearer {access_token}"}

    base_url = "https://api.gfm.eodc.eu/v1"

    if not output_file_path:
        base_file_path = "./output"

    product_id = product["product_id"]
    product_time = product["product_time"]

    output_file_path = f"{base_file_path}"
    Path(output_file_path).mkdir(parents=True, exist_ok=True)

    print(f"Downloading product: {product_id}")

    download_url = f"{base_url}/download/product/{product_id}"
    response = requests.get(download_url, headers=header)
    download_link = response.json()["download_link"]

    # Download and unzip file
    r = requests.get(download_link)
    buffer = io.BytesIO(r.content)
    hf_api = hf_utils.get_hf_api()

    with zipfile.ZipFile(buffer, "r") as z:
        namelist = z.namelist()
        for name in namelist:
            if "FLOOD" in name and ".geojson" in name:
                flood_filename = name
                path_in_repo = f"flood-geojson/{flood_filename}"
                break
        with z.open(flood_filename) as f:
            hf_api.upload_file(
                path_or_fileobj=f,
                path_in_repo=path_in_repo,
                repo_id="rodekruis/flood-mapping",
                repo_type="dataset",
            )

    df = pd.DataFrame(
        {
            "aoi_id": [area_id],
            "datetime": [product_time],
            "product": [product_id],
            "path_in_repo": [path_in_repo],
        }
    )

    index_df = hf_utils.get_geojson_index_df()
    index_df = pd.concat([index_df, df], ignore_index=True)
    hf_utils.update_geojson_index_df(index_df)

    print(f"Product {product_id} downloaded succesfully")


# Gets all AOIs and transforms them to a dict with some features that are useful in the app, like the bbox
@st.cache_resource
def retrieve_all_aois():
    print("Retrieving all AOIs from GFM API")
    user_id, access_token = get_gfm_user_and_token()
    header = {"Authorization": f"bearer {access_token}"}

    base_url = "https://api.gfm.eodc.eu/v1"

    aoi_url = f"{base_url}/aoi/user/{user_id}"
    response = requests.get(aoi_url, headers=header)

    aois = response.json()["aois"]

    aois = {
        aoi["aoi_id"]: {
            "name": aoi["aoi_name"],
            "bbox": aoi["geoJSON"],
            "name_id_preview": f"{aoi['aoi_name']} - {aoi['aoi_id'][:6]}...",
        }
        for aoi in aois
    }

    return aois


# Creates AOI on GFM using API
def create_aoi(new_area_name, coordinates):
    user_id, access_token = get_gfm_user_and_token()
    header = {"Authorization": f"bearer {access_token}"}

    base_url = "https://api.gfm.eodc.eu/v1"

    # Create area of impact
    print("Creating new area of impact")
    create_aoi_url = f"{base_url}/aoi/create"

    payload = {
        "aoi_name": new_area_name,
        "description": new_area_name,
        "user_id": user_id,
        "geoJSON": {"type": "Polygon", "coordinates": coordinates},
    }

    r = requests.post(url=create_aoi_url, json=payload, headers=header)
    r.raise_for_status()
    print("Posted new AOI")


# Deletes AOI on GFM using API
def delete_aoi(aoi_id):
    user_id, access_token = get_gfm_user_and_token()
    header = {"Authorization": f"bearer {access_token}"}

    base_url = "https://api.gfm.eodc.eu/v1"

    # Create area of impact
    print(f"Deleting area of impact {aoi_id}")
    delete_aoi_url = f"{base_url}/aoi/delete/id/{aoi_id}"
    print(delete_aoi_url)

    r = requests.delete(url=delete_aoi_url, headers=header)
    r.raise_for_status()
    print("AOI deleted")
