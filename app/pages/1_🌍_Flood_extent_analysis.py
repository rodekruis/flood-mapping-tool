import json
from pathlib import Path

import folium
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

# Sync cached data
# ! WARNING: will erase your output folder
# # # sync_cached_data()

# Create two rows: top and bottom panel
row1 = st.container()
# Crate two columns in the top panel: input map and paramters
col1, col2 = row1.columns([2, 1])
feat_group_selected_area = folium.FeatureGroup(name="selected_area")
with col1:
    with open("./bboxes/bboxes.json", "r") as f:
        bboxes = json.load(f)
    selected_area = st.selectbox("Select saved area", options=bboxes.keys())

    # retrieve and select available dates
    if selected_area:
        area_folder = Path(f"./output/{selected_area}")
        if area_folder.exists():
            available_product_times = [
                str(f.name) for f in area_folder.iterdir() if f.is_dir()
            ]

            available_product_times = [
                prod_time.replace("_", ":") for prod_time in available_product_times
            ]
            selected_product_time = st.selectbox(
                "Select available date range", options=available_product_times
            )
        else:
            selected_product_time = None

        # display the bounding box
        bounding_box = bboxes[selected_area]["bounding_box"]
        geojson_selected_area = folium.GeoJson(bounding_box)
        feat_group_selected_area.add_child(geojson_selected_area)

        # geojson_selected_area = folium.GeoJson(bboxes[selected_area])
        # feat_group_selected_area.add_child(geojson_selected_area)
        if selected_product_time:
            geojson_flood_area = get_existing_flood_geojson(
                selected_area, selected_product_time
            )
            feat_group_selected_area.add_child(geojson_flood_area)

    # Add collapsable container for input map
    with st.expander("Input map", expanded=True):
        # Create folium map
        # call to render Folium map in Streamlit
        folium_map = folium.Map([39, 0], zoom_start=8)
        # check if the FeatureGroup has any children (i.e., layers added)
        if len(feat_group_selected_area._children) > 0:
            # if there is data, fit the map to the bounds
            folium_map.fit_bounds(feat_group_selected_area.get_bounds())
        else:
            # if there is no data, set a default view
            # this is necessary to start up the page
            folium_map = folium.Map(location=[39, 0], zoom_start=8)

        m = st_folium(
            folium_map,
            width=800,
            height=450,
            feature_group_to_add=feat_group_selected_area,
        )
with col2:
    # Add collapsable container for image dates
    with st.expander("Choose Dates", expanded=True):
        start_date = st.date_input("Start date")
        end_date = st.date_input("End date")
    # Add collapsable container for parameters
    with st.expander("Choose Parameters"):
        # Add slider for threshold
        st.text("Add relevant (API) parameters here")

    submitted = st.button("Update flood extent")


# If the button is clicked do the following
if submitted:
    with col2:
        # Some basic validation on dates and that there's an area if relevant
        get_gfm = True
        check_dates = start_date <= end_date

        # Output error if dates are not valid
        if not check_dates:
            st.error("Make sure that the dates were inserted correctly")
            get_gfm = False

        # Only if checks pass go and get the GFM data
        if get_gfm:
            # Show loader because it will take a while
            with st.spinner("Getting GFM files... Please wait..."):
                # download_gfm_geojson(area_name)
                download_gfm_geojson(
                    selected_area, from_date=start_date, to_date=end_date
                )

            # Display that getting the files is finished
            st.markdown("Getting GFM files finished")
