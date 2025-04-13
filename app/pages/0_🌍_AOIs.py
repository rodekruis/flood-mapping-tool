import folium
import streamlit as st
from folium.plugins import Draw
from src.config_parameters import params
from src.gfm import GFMHandler
from src.utils import (
    add_about,
    get_aoi_id_from_selector_preview,
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

# Initialize GFMHandler if not already in session state
if "gfm_handler" not in st.session_state:
    st.session_state["gfm_handler"] = GFMHandler()

# Page title
st.markdown("# AOIs")

# Set page style
set_tool_page_style()

row1 = st.container()
save_area = False

# To track whether radio selector was changed to reload AOIs if necessary, initialised as See Areas to prevent double loading
if "prev_radio_selection" not in st.session_state:
    st.session_state["prev_radio_selection"] = "See Areas"

if "all_aois" not in st.session_state:
    st.session_state["all_aois"] = st.session_state["gfm_handler"].retrieve_all_aois()


feat_group_selected_area = folium.FeatureGroup(name="selected_area")
radio_selection = st.radio(
    label="Action Type",
    options=["See Areas", "Create New Area", "Delete Area"],
    label_visibility="hidden",
)

# call to render Folium map in Streamlit
folium_map = folium.Map([39, 0], zoom_start=8)

# See Areas will show all areas collected from GFM.
# Collecting AOIs is done on first page load and when switching from a different radio selection back to See Areas
if radio_selection == "See Areas":
    if st.session_state["prev_radio_selection"] != "See Areas":
        st.session_state["all_aois"] = st.session_state[
            "gfm_handler"
        ].retrieve_all_aois()

    # Add each AOI as a feature group to the map
    for aoi in st.session_state["all_aois"].values():
        feat_group_selected_area.add_child(folium.GeoJson(aoi["bbox"]))

    folium_map.fit_bounds(feat_group_selected_area.get_bounds())
    st.session_state["prev_radio_selection"] = "See Areas"

# When creating a new area the map will have a rectangle drawing option which will be saved with Save button
elif radio_selection == "Create New Area":
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

    # Add geocoder search bar
    from folium.plugins import Geocoder
    Geocoder(
        position="topleft",
        collapsed=True,
        add_marker=False, # ! Adding a marker messes up the area selection tool
        zoom=10
    ).add_to(folium_map)

    new_area_name = st.text_input("Area name")
    
    # Check if the name already exists
    existing_names = [aoi["name"] for aoi in st.session_state["all_aois"].values()]
    is_name_valid = new_area_name and new_area_name not in existing_names
    
    if new_area_name and not is_name_valid:
        st.error(f"An area with the name '{new_area_name}' already exists. Please choose a different name.")
    
    save_area = st.button("Save Area", disabled=not is_name_valid)

    st.session_state["prev_radio_selection"] = "Create New Area"

# Delete area does exactly that, it will show the selected area and a delete button
elif radio_selection == "Delete Area":
    existing_areas = [
        aoi["name_id_preview"] for aoi in st.session_state["all_aois"].values()
    ]

    area_to_delete_name_id = st.selectbox(
        "Choose area to delete", options=existing_areas
    )
    selected_area_id = get_aoi_id_from_selector_preview(
        st.session_state["all_aois"], area_to_delete_name_id
    )

    bbox = st.session_state["all_aois"][selected_area_id]["bbox"]
    feat_group_selected_area.add_child(folium.GeoJson(bbox))
    folium_map.fit_bounds(feat_group_selected_area.get_bounds())

    delete_area = st.button("Delete")
    st.session_state["prev_radio_selection"] = "Delete Area"

    # If clicked will delete both from API and the session state to also remove from the Delete Area selector
    if delete_area:
        st.session_state["gfm_handler"].delete_aoi(selected_area_id)
        st.session_state["all_aois"].pop(selected_area_id, None)
        st.toast("Area successfully deleted")
        st.rerun()

# Create map with features based on the radio selector handling above
m = st_folium(
    folium_map,
    width=800,
    height=450,
    feature_group_to_add=feat_group_selected_area,
)

# If in Create New Area the save button is clicked it will write the new area to the API
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

        st.session_state["gfm_handler"].create_aoi(new_area_name, coordinates)
        st.toast("Area successfully created")

st.session_state["prev_page"] = "aois"
