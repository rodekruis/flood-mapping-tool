from datetime import date, timedelta

import folium
import pandas as pd
import streamlit as st
from src import hf_utils
from src.config_parameters import params
from src.gfm import get_cached_aois, get_cached_gfm_handler
from src.utils import (
    add_about,
    get_aoi_id_from_selector_preview,
    get_existing_geojson,
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
# Create two columns in the top panel: input map and paramters
col1, col2, col3, col4 = row1.columns([1, 1, 1, 2])
col2_1, col2_2 = row2.columns([3, 2])

# Retrieve GFM Handler and AOIs to fill AOI selector
gfm = get_cached_gfm_handler()
aois = get_cached_aois()


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
        options=[aoi["name_id_preview"] for aoi in aois.values()],
        on_change=on_area_selector_change,
    )

    selected_area_id = get_aoi_id_from_selector_preview(aois, selected_area_name_id)

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
    show_available_products = st.button("Show GFM products")

# If button above is triggered, get products from GFM
# Then save all products to the session state and rerun the app to display them
if show_available_products:
    products = gfm.get_area_products(selected_area_id, start_date, end_date)
    st.session_state["all_products"] = products
    st.rerun()

# Contains the product checkboxes if they exist after pushing the "Show available products" button
with col2_2:
    row_checkboxes = st.container()
    row_buttons = st.container()

with row_checkboxes:
    checkboxes = list()
    # Products are checked against the index to check whether they are already downloaded
    index_df = hf_utils.get_geojson_index_df()
    if st.session_state["all_products"]:
        # Get unique product time groups
        unique_time_groups = set()
        for product in st.session_state["all_products"]:
            unique_time_groups.add(product["product_time_group"])

        # Create dataframe for the table
        product_data = []
        for time_group in sorted(unique_time_groups):
            # Check if any product in this group is already downloaded
            products_in_group = [
                p
                for p in st.session_state["all_products"]
                if p["product_time_group"] == time_group
            ]

            dataset_link = ""
            for product in products_in_group:
                if product["product_id"] in index_df["product"].values:
                    available_status = "Available in Floodmap"
                    flood_geojson_path = index_df.loc[
                        index_df["product"] == product["product_id"],
                        "flood_geojson_path",
                    ].values[0]
                    dataset_link = f"https://huggingface.co/datasets/rodekruis/flood-mapping/resolve/main/{flood_geojson_path}?download=true"

            product_data.append(
                {
                    "Check": False,
                    "Product time": time_group,
                    "Available": dataset_link,
                }
            )

        product_groups_df = pd.DataFrame(product_data)

        # Create the data editor with checkbox column
        product_groups_st_df = st.data_editor(
            product_groups_df,
            column_config={
                "Check": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select products to process",
                    default=False,
                ),
                "Product time": st.column_config.TextColumn(
                    "Product Time Group", disabled=True
                ),
                "Available": st.column_config.LinkColumn("Available in dataset"),
            },
            hide_index=True,
            disabled=["Product time", "Available"],
        )

        # Convert checkbox states to list for compatibility with existing code
        checkboxes = product_groups_st_df["Check"].tolist()

with row_buttons:
    below_checkbox_col1, below_checkbox_col2 = row_buttons.columns([1, 1])

# Contains the "Download Products" button
with below_checkbox_col1:
    st.text(
        "Button info",
        help=""
        """
    Will download the selected products from GFM to the Floodmap app
    (click "Show available products" first if there are none).
    Products that show that they have already been downloaded can be left checked,
    they will be skipped.
    """,
    )
    download_products = st.button("Download to Floodmap")

    # If the button is clicked download all checked products that have not been downloaded yet
    if download_products:
        index_df = hf_utils.get_geojson_index_df()
        # Get selected time groups from the table
        selected_time_groups = product_groups_st_df[product_groups_st_df["Check"]][
            "Product time"
        ].tolist()

        # For each selected time group
        for time_group in selected_time_groups:
            # Get all products for this time group
            products_in_group = [
                p
                for p in st.session_state["all_products"]
                if p["product_time_group"] == time_group
            ]

            # Download each product in the group that hasn't been downloaded yet
            for product_to_download in products_in_group:
                if product_to_download["product_id"] not in index_df["product"].values:
                    with st.spinner(
                        f"Getting GFM files for {product_to_download['product_time']}, this may take a couple of minutes"
                    ):
                        gfm.download_flood_product(
                            selected_area_id, product_to_download
                        )
        st.rerun()

# For all the selected products add them to the map if they are available
feature_groups = []
flood_featuregroup = None
selected_geojsons = []
if st.session_state["all_products"]:
    index_df = hf_utils.get_geojson_index_df()
    # Get unique time groups
    unique_time_groups = sorted(
        set(p["product_time_group"] for p in st.session_state["all_products"])
    )

    # For each checkbox (which corresponds to a time group)
    for i, checkbox in enumerate(checkboxes):
        if checkbox:
            time_group = unique_time_groups[i]
            # Get all products for this time group
            products_in_group = [
                p
                for p in st.session_state["all_products"]
                if p["product_time_group"] == time_group
            ]

            # Create a feature group for this time group
            flood_featuregroup = folium.FeatureGroup(name=time_group)
            footprint_featuregroup = folium.FeatureGroup(name="Sentinel footprint")
            group_has_features = False

            # Add all available products from this group to the feature group
            for product in products_in_group:
                if product["product_id"] in index_df["product"].values:
                    # Get the raw geojsons for further usage in the app
                    flood_geojson = get_existing_geojson(product["product_id"], "flood")
                    selected_geojsons.append(flood_geojson)
                    # Convert geojsons to folium features to display on the map
                    flood_folium_geojson = folium.GeoJson(
                        flood_geojson,
                        style_function=lambda x: {
                            "fillColor": "#ff0000",
                            "color": "#ff0000",
                            "fillOpacity": 0.2,
                        },
                    )
                    flood_featuregroup.add_child(flood_folium_geojson)

                    footprint_geojson = get_existing_geojson(
                        product["product_id"], "footprint"
                    )
                    footprint_folium_geojson = folium.GeoJson(
                        footprint_geojson,
                        style_function=lambda x: {
                            "fillColor": "yellow",
                            "color": "yellow",
                            "fillOpacity": 0.2,
                            "weight": 0,
                        },
                    )
                    footprint_featuregroup.add_child(footprint_folium_geojson)
                    group_has_features = True

            # Only add the feature group if it contains any features
            if group_has_features:
                feature_groups.append(flood_featuregroup)
                feature_groups.append(footprint_featuregroup)

# Contains the map
with col2_1:
    if selected_area_id:
        # display the bounding box
        bounding_box = aois[selected_area_id]["bbox"]
        geojson_selected_area = folium.GeoJson(
            bounding_box,
            style_function=lambda x: {"fillOpacity": 0.2, "weight": 1},
        )
        feat_group_selected_area = folium.FeatureGroup(name="selected_area")
        feat_group_selected_area.add_child(geojson_selected_area)
        feature_groups.append(feat_group_selected_area)

    # Create folium map
    folium_map = folium.Map([39, 0], zoom_start=8)
    folium_map.fit_bounds(feat_group_selected_area.get_bounds())

    m = st_folium(
        folium_map, width=800, height=450, feature_group_to_add=feature_groups
    )

    if flood_featuregroup:
        flood_part_of_legend = """
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background:  rgba(255, 0, 0, .2); border: 1px solid red;"></div>
            <div style="margin-left: 5px;">Floods</div>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background:  rgba(255, 255, 0, .2); border: 1px solid yellow;"></div>
            <div style="margin-left: 5px;">Sentinel Footprint</div>
        </div>
        """
    else:
        flood_part_of_legend = ""
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 20px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background:  rgba(51, 136, 255, .2); border: 1px solid #3388ff;"></div>
                <div style="margin-left: 5px;">AOI</div>
            </div>
            {flood_part_of_legend}
        </div>
        """,
        unsafe_allow_html=True,
    )


# Keep track of which page we're currently on for page switch events
st.session_state["prev_page"] = "flood_extent"
