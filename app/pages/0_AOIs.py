import json
import os
from pathlib import Path

import folium
import requests
import streamlit as st
from folium.plugins import Draw
from src.config_parameters import params
from src.gfm import download_gfm_geojson, get_existing_flood_geojson, sync_cached_data
from src.utils import (
    add_about,
    set_tool_page_style,
    toggle_menu_button,
)
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(layout="wide", page_title=params["browser_title"])

# If app is deployed hide menu button
toggle_menu_button()

# Create sidebar
add_about()

# Page title
st.markdown("# Flood extent analysis")

# Set page style
set_tool_page_style()

# Create two rows: top and bottom panel
row1 = st.container()
save_area = False

with row1:
    action_type = st.radio(
        label="Action Type",
        options=["See Areas", "Create New Area", "Delete Area"],
        label_visibility="hidden",
    )

    # call to render Folium map in Streamlit
    folium_map = folium.Map([39, 0], zoom_start=8)
    feat_group_selected_area = folium.FeatureGroup(name="selected_area")

    if action_type == "See Areas":
        with open("./bboxes/bboxes.json", "r") as f:
            bboxes = json.load(f)
        for area_name in bboxes.keys():
            bbox = bboxes[area_name]["bounding_box"]
            feat_group_selected_area.add_child(folium.GeoJson(bbox))

        folium_map.fit_bounds(feat_group_selected_area.get_bounds())

    elif action_type == "Create New Area":
        Draw(
            export=False,
            draw_options={
                "circle": False,
                "polyline": False,
                "polygon": False,
                "rectangle": True,
                "marker": False,
                "circlemarker": False,
            },
        ).add_to(folium_map)

        new_area_name = st.text_input("Area name")
        save_area = st.button("Save Area")

    elif action_type == "Delete Area":
        # Load existing bboxes
        with open("./bboxes/bboxes.json", "r") as f:
            bboxes = json.load(f)
            existing_areas = bboxes.keys()

        area_to_delete = st.selectbox("Choose area to delete", options=existing_areas)
        bbox = bboxes[area_to_delete]["bounding_box"]
        feat_group_selected_area.add_child(folium.GeoJson(bbox))
        folium_map.fit_bounds(feat_group_selected_area.get_bounds())

        delete_area = st.button("Delete")

        if delete_area:
            with open("./bboxes/bboxes.json", "r") as f:
                bboxes = json.load(f)
            bboxes.pop(area_to_delete, None)
            with open("./bboxes/bboxes.json", "w") as f:
                json.dump(bboxes, f)
            st.toast("Area successfully deleted")

    with open("./bboxes/bboxes.json", "r") as f:
        bboxes = json.load(f)

    # geojson_catania = get_existing_flood_geojson("Catania")
    # print(geojson_catania)
    # geojson_selected_area = folium.GeoJson(geojson_catania)

    # feat_group_selected_area.add_child(geojson_selected_area)
    m = st_folium(
        folium_map,
        width=800,
        height=450,
        feature_group_to_add=feat_group_selected_area,
    )

    if save_area:
        check_drawing = m["all_drawings"] != [] and m["all_drawings"] is not None
        if not check_drawing:
            st.error("Please create a region using the rectangle tool on the map.")
        elif new_area_name == "":
            st.error("Please provide a name for the new area")
        else:
            # Get the drawn area
            selected_area_geojson = m["all_drawings"][-1]

            print("starting to post new area name to gfm api")
            coordinates = selected_area_geojson["geometry"]["coordinates"]

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

            print("authenticated to API")
            # Create area of impact
            create_aoi_url = f"{base_url}/aoi/create"

            payload = {
                "aoi_name": new_area_name,
                "description": new_area_name,
                "user_id": user_id,
                "geoJSON": {"type": "Polygon", "coordinates": coordinates},
            }

            r = requests.post(url=create_aoi_url, json=payload, headers=header)
            print(r.json())
            print("Posted new AOI")

            print("Writing new area to bbox json")
            # Load existing bboxes
            with open("./bboxes/bboxes.json", "r") as f:
                bboxes = json.load(f)

            # If the    area doesn't exist, create it
            if new_area_name not in bboxes:
                bboxes[new_area_name] = {}

            # Save the new bounding box under the date range key
            bboxes[new_area_name] = {
                "bounding_box": selected_area_geojson,
                "date_ranges": [],  # Will be populated when files are downloaded
            }
            # Write the updated data back to file
            with open("./bboxes/bboxes.json", "w") as f:
                json.dump(bboxes, f, indent=4)

            st.toast("Area successfully created")
