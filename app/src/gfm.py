import io
import os
import zipfile
from datetime import datetime, timedelta

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


class GFMHandler:
    def __init__(self):
        self.base_url = "https://api.gfm.eodc.eu/v1"
        self.user_id, self.access_token = self._get_gfm_user_and_token()
        self.header = {"Authorization": f"bearer {self.access_token}"}

    def _get_gfm_user_and_token(self):
        username = os.environ["gfm_username"]
        password = os.environ["gfm_password"]

        # Get token, setup header
        token_url = f"{self.base_url}/auth/login"
        payload = {"email": username, "password": password}

        response = requests.post(token_url, json=payload)
        user_id = response.json()["client_id"]
        access_token = response.json()["access_token"]
        print("retrieved user id and access token")

        return user_id, access_token

    def _refresh_token(self):
        """Refresh the access token and update the authorization header"""
        self.user_id, self.access_token = self._get_gfm_user_and_token()
        self.header = {"Authorization": f"bearer {self.access_token}"}
        print("Refreshed access token")

    def _make_request(self, method, url, **kwargs):
        """Make an API request with automatic token refresh on authentication failure"""
        try:
            response = requests.request(method, url, headers=self.header, **kwargs)
            if response.status_code == 401:  # Unauthorized
                print("Token expired, refreshing...")
                self._refresh_token()
                # Retry the request with new token
                response = requests.request(method, url, headers=self.header, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise

    def get_area_products(self, area_id, from_date, to_date):
        params = {
            "time": "range",
            "from": f"{from_date}T00:00:00",
            "to": f"{to_date}T00:00:00",
        }
        prod_url = f"{self.base_url}/aoi/{area_id}/products"
        response = self._make_request("GET", prod_url, params=params)
        products = response.json()["products"]
        print(f"Found {len(products)} products for {area_id}")

        # Sort products by timestamp
        products.sort(key=lambda x: x["product_time"])

        # Group products that are within 1 minute of each other
        if products:
            current_group_time = products[0]["product_time"]
            products[0]["product_time_group"] = current_group_time

            for i in range(1, len(products)):
                product_time = datetime.fromisoformat(
                    products[i]["product_time"].replace("Z", "+00:00")
                )
                current_time = datetime.fromisoformat(
                    current_group_time.replace("Z", "+00:00")
                )
                time_diff = product_time - current_time

                # If more than 1 minute apart, start a new group
                if time_diff > timedelta(minutes=1):
                    current_group_time = products[i]["product_time"]

                products[i]["product_time_group"] = current_group_time

        return products

    def download_flood_product(self, area_id, product):
        product_id = product["product_id"]
        product_time = product["product_time"]

        print(f"Downloading product: {product_id}")

        download_url = f"{self.base_url}/download/product/{product_id}"
        response = self._make_request("GET", download_url)
        download_link = response.json()["download_link"]

        # Download and unzip file
        r = requests.get(download_link)
        buffer = io.BytesIO(r.content)
        hf_api = hf_utils.get_hf_api()

        data = {
            "aoi_id": area_id,
            "datetime": product_time,
            "product": product_id,
        }

        with zipfile.ZipFile(buffer, "r") as z:
            namelist = z.namelist()

            for file_type in ["flood", "footprint"]:
                filename = next(
                    name
                    for name in namelist
                    if file_type in name.lower() and name.endswith(".geojson")
                )

                path_in_repo = f"flood-geojson/{filename}"

                with z.open(filename) as f:
                    hf_api.upload_file(
                        path_or_fileobj=f,
                        path_in_repo=path_in_repo,
                        repo_id="rodekruis/flood-mapping",
                        repo_type="dataset",
                    )

                data[f"{file_type}_geojson_path"] = path_in_repo

        df = pd.DataFrame([data])

        index_df = hf_utils.get_geojson_index_df()
        index_df = pd.concat([index_df, df], ignore_index=True)
        hf_utils.update_geojson_index_df(index_df)

        print(f"Product {product_id} downloaded succesfully")

    def retrieve_all_aois(self):
        print("Retrieving all AOIs from GFM API")
        aoi_url = f"{self.base_url}/aoi/user/{self.user_id}"
        response = self._make_request("GET", aoi_url)

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

    def create_aoi(self, new_area_name, coordinates):
        print("Creating new area of impact")
        create_aoi_url = f"{self.base_url}/aoi/create"

        payload = {
            "aoi_name": new_area_name,
            "description": new_area_name,
            "user_id": self.user_id,
            "geoJSON": {"type": "Polygon", "coordinates": coordinates},
        }

        self._make_request("POST", create_aoi_url, json=payload)
        get_cached_aois.clear()
        print("Posted new AOI")

    def delete_aoi(self, aoi_id):
        print(f"Deleting area of impact {aoi_id}")
        delete_aoi_url = f"{self.base_url}/aoi/delete/id/{aoi_id}"
        print(delete_aoi_url)

        self._make_request("DELETE", delete_aoi_url)
        get_cached_aois.clear()
        print("AOI deleted")


@st.cache_resource
def get_cached_gfm_handler():
    return GFMHandler()


@st.cache_resource
def get_cached_aois():
    gfm = get_cached_gfm_handler()
    return gfm.retrieve_all_aois()
