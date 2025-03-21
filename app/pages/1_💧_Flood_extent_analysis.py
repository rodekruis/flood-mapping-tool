from datetime import date, timedelta

import folium
import pandas as pd
import streamlit as st
from src.config_parameters import params
from src.gfm import (
    download_flood_product,
    get_area_products,
    retrieve_all_aois,
)
from src.utils import (
    add_about,
    get_aoi_id_from_selector_preview,
    get_existing_flood_geojson,
    set_tool_page_style,
    toggle_menu_button,
)
from streamlit_folium import st_folium

today = date.today()

default_date_yesterday = today - timedelta(days=1)

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
row2 = st.container()
# Crate two columns in the top panel: input map and paramters
col1, col2, col3, col4, col5 = row1.columns([1, 1, 1, 1, 1])
col2_1, col2_2 = row2.columns([3, 2])

# Retrieve AOIs to fill AOI selector
if "all_aois" not in st.session_state:
    st.session_state["all_aois"] = retrieve_all_aois()

# If coming from a different page, all aois may be filled but not up to date, retrigger
if st.session_state["prev_page"] != "flood_extent":
    st.session_state["all_aois"] = retrieve_all_aois()

if "all_products" not in st.session_state:
    st.session_state["all_products"] = None


# To force removing product checkboxes when AOI selector changes
def on_area_selector_change():
    print("Area selector changed, removing product checkboxes")
    st.session_state["all_products"] = None


# Contains AOI selector
with col1:
    selected_area_name_id = st.selectbox(
        "Select saved AOI",
        options=[
            aoi["name_id_preview"] for aoi in st.session_state["all_aois"].values()
        ],
        on_change=on_area_selector_change,
    )

    selected_area_id = get_aoi_id_from_selector_preview(
        st.session_state["all_aois"], selected_area_name_id
    )

# Contain datepickers
with col2:
    today = date.today()
    two_weeks_ago = today - timedelta(days=14)
    start_date = st.date_input("Start date", value=two_weeks_ago)

with col3:
    end_date = st.date_input("End date", value=today)

# Contains available products button
with col4:
    st.text(
        "Button info",
        help="""
    This will show the timestamps of all available GFM products
    that intersect with the AOI for the selected date range.
    Getting the available products is a relatively fast operation
    it will not trigger any product downloads.
    """,
    )
    show_available_products = st.button("Show available products")

# If button above is triggered, get products from GFM
# Then save all products to the session state and rerun the app to display them
if show_available_products:
    products = get_area_products(selected_area_id, start_date, end_date)
    st.session_state["all_products"] = products
    st.rerun()

# Contains the product checkboxes if they exist after pushing the "Show available products" button
with col2_2:
    checkboxes = list()
    # Products are checked against the index to check whether they are already downloaded
    index_df = pd.read_csv("./output/index.csv")
    if st.session_state["all_products"]:
        for product in st.session_state["all_products"]:
            suffix = ""
            if product["product_id"] in index_df["product"].values:
                suffix = " - Already Downloaded"
            checkbox = st.checkbox(product["product_time"] + suffix)
            checkboxes.append(checkbox)

# Contains the "Download Products" button
with col5:
    st.text(
        "Button info",
        help=""
        """
    Will download the selected products (click "Show available products"
    first if there are none). Products that show that they have already
    been downloaded can be left checked, they will be skipped.
    """,
    )
    download_products = st.button("Download products")

    # If the button is clicked download all checked products that have not been downloaded yet
    if download_products:
        index_df = pd.read_csv("./output/index.csv")
        for i, checkbox in enumerate(checkboxes):
            if checkbox:
                product_to_download = st.session_state["all_products"][i]
                if product_to_download["product_id"] not in index_df["product"].values:
                    with st.spinner(
                        f"Getting GFM files for {product_to_download['product_time']}, this may take a couple of minutes"
                    ):
                        download_flood_product(selected_area_id, product_to_download)
        st.rerun()

# For all the selected products add them to the map if they are available
feature_groups = []
if st.session_state["all_products"]:
    index_df = pd.read_csv("./output/index.csv")
    for i, checkbox in enumerate(checkboxes):
        if checkbox:
            product_id = st.session_state["all_products"][i]["product_id"]
            if product_id in index_df["product"].values:
                feat_group_flood = get_existing_flood_geojson(product_id)
                feature_groups.append(feat_group_flood)

# Contains the map
with col2_1:
    if selected_area_id:
        # display the bounding box
        bounding_box = st.session_state["all_aois"][selected_area_id]["bbox"]
        geojson_selected_area = folium.GeoJson(bounding_box)
        feat_group_selected_area = folium.FeatureGroup(name="selected_area")
        feat_group_selected_area.add_child(geojson_selected_area)
        feature_groups.append(feat_group_selected_area)

    # Create folium map
    folium_map = folium.Map([39, 0], zoom_start=8)
    folium_map.fit_bounds(feat_group_selected_area.get_bounds())

    m = st_folium(
        folium_map,
        width=800,
        height=450,
        feature_group_to_add=feature_groups,
    )

# Keep track of which page we're currently on for page switch events
st.session_state["prev_page"] = "flood_extent"
