import json
from pathlib import Path

import folium
import streamlit as st
from folium.plugins import Draw
from src.config_parameters import params
from src.gfm import download_gfm_geojson, get_existing_flood_geojson
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
# Crate two columns in the top panel: input map and paramters
col1, col2 = row1.columns([2, 1])
feat_group_selected_area = folium.FeatureGroup(name="selected_area")
with col1:
    area_type = st.radio(label="", options=["Existing area", "New area"])
    if area_type == "Existing area":
        with open("./bboxes/bboxes.json", "r") as f:
            bboxes = json.load(f)
        selected_area = st.selectbox("Select saved area", options=bboxes.keys())
        geojson_selected_area = folium.GeoJson(bboxes[selected_area])
        feat_group_selected_area.add_child(geojson_selected_area)
        geojson_flood_area = get_existing_flood_geojson(selected_area)
        feat_group_selected_area.add_child(geojson_flood_area)

    elif area_type == "New area":
        new_area_name = st.text_input("Area name")
    # Add collapsable container for input map
    with st.expander("Input map", expanded=True):
        # Create folium map
        # call to render Folium map in Streamlit
        folium_map = folium.Map([39, 0], zoom_start=8)
        # Add drawing tools to map
        if area_type == "New area":
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

        m = st_folium(
            folium_map,
            width=800,
            height=450,
            feature_group_to_add=feat_group_selected_area,
        )
with col2:
    # Add collapsable container for image dates
    with st.expander("Choose Image Dates"):
        start_date = st.date_input("Start date")
        end_date = st.date_input("End date")
    # Add collapsable container for parameters
    with st.expander("Choose Parameters"):
        # Add slider for threshold
        st.text("Add relevant (API) parameters here")

    # Button to trigger GFM data retrieval
    if area_type == "New area":
        button_text = "Get new flood extent"
    else:
        button_text = "Update flood extent"
    submitted = st.button(button_text)


# If the button is clicked do the following
if submitted:
    with col2:
        # Some basic validation on dates and that there's an area if relevant
        get_gfm = True
        check_dates = start_date <= end_date
        if area_type == "New area":
            check_drawing = m["all_drawings"] != [] and m["all_drawings"] is not None

        # Output error if dates are not valid
        if not check_dates:
            st.error("Make sure that the dates were inserted correctly")
            get_gfm = False
        # Output error if no polygons were drawn
        if area_type == "New area":
            if not check_drawing:
                st.error("Please create a region using the rectangle tool on the map.")
                get_gfm = False
            elif new_area_name == "":
                st.error("Please provide a name for the new area")
                get_gfm = False

        # Only if checks pass go and get the GFM data
        if get_gfm:
            if area_type == "Existing area":
                area_name = selected_area
            elif area_type == "New area":
                area_name = new_area_name

            # Show loader because it will take a while
            with st.spinner("Getting GFM files... Please wait..."):
                # If a new area save the bounding box
                if area_type == "New area":
                    # Save bounding box
                    with open("./bboxes/bboxes.json", "r") as f:
                        bboxes = json.load(f)
                        selected_area_geojson = m["all_drawings"][-1]
                        bboxes[new_area_name] = selected_area_geojson
                    with open("./bboxes/bboxes.json", "w") as f:
                        json.dump(bboxes, f)

                    # Download files, for a new area also get coordinates to save to GFM
                    coords = selected_area_geojson["geometry"]["coordinates"][0]
                    download_gfm_geojson(area_name, new_coordinates=coords)

                # For an existing area just get the latest update from GFM
                if area_type == "Existing area":
                    download_gfm_geojson(area_name)

            # Display that getting the files is finished
            st.markdown("Getting GFM files finished")
