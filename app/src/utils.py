"""Functions for the layout of the Streamlit app, including the sidebar."""

import io
import json
import os
import zipfile

import pandas as pd
import streamlit as st

from src.config_parameters import params


def get_aoi_id_from_selector_preview(all_aois, name_id_preview):
    for aoi_id, aoi in all_aois.items():
        if aoi["name_id_preview"] == name_id_preview:
            return aoi_id


# Check if app is deployed
def is_app_on_streamlit():
    """Check whether the app is on streamlit or runs locally."""
    return "HOSTNAME" in os.environ and os.environ["HOSTNAME"] == "streamlit"


# General layout
def toggle_menu_button():
    """If app is on streamlit, hide menu button."""
    if is_app_on_streamlit():
        st.markdown(
            """
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
        """,
            unsafe_allow_html=True,
        )


# Home page
def set_home_page_style():
    """Set style home page."""
    st.markdown(
        """
    <style> p { font-size: %s; } </style>
    """
        % params["docs_fontsize"],
        unsafe_allow_html=True,
    )


# Documentation page
def set_doc_page_style():
    """Set style documentation page."""
    st.markdown(
        """
    <style> p { font-size: %s; } </style>
    """
        % params["docs_fontsize"],
        unsafe_allow_html=True,
    )


# Tool page
def set_tool_page_style():
    """Set style tool page."""
    st.markdown(
        """
            <style>
                .streamlit-expanderHeader {
                    font-size: %s;
                    color: #000053;
                }
                .stDateInput > label {
                    font-size: %s;
                }
                .stSlider > label {
                    font-size: %s;
                }
                .stRadio > label {
                    font-size: %s;
                }
                .stButton > button {
                    font-size: %s;
                    font-weight: %s;
                    background-color: %s;
                }
            </style>
        """
        % (
            params["expander_header_fontsize"],
            params["widget_header_fontsize"],
            params["widget_header_fontsize"],
            params["widget_header_fontsize"],
            params["button_text_fontsize"],
            params["button_text_fontweight"],
            params["button_background_color"],
        ),
        unsafe_allow_html=True,
    )


# Sidebar
def add_about():
    """
    Add about and contacts to sidebar.

    Inputs:
        None
    Returns:
        None
    """
    # About textbox
    st.sidebar.markdown("## About")
    st.sidebar.markdown(
        f"""
        <p>
            Todo: general about stuff <br />
            <a href='{params["url_github_repo"]}'>
            Github Repo</a>
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Contacts textbox
    st.sidebar.markdown(" ")
    st.sidebar.markdown("## Contacts")

    # Add data scientists and emails
    contacts_text = ""
    for ds, email in params["data_scientists"].items():
        contacts_text += ds + (
            "<span style='float:right; margin-right: 3px;'>"
            "<a href='mailto:%s'>%s</a></span><br>" % (email, email)
        )

    # Add text box
    st.sidebar.markdown(
        """
        <div class='warning' style='
            background-color: %s;
            margin: 0px;
            padding: 1em;'
        '>
            <p style='
                margin-left:1em;
                font-size: 1rem;
                margin: 0px
            '>
                %s
            </p>
        </div>
        """
        % (params["about_box_background_color"], contacts_text),
        unsafe_allow_html=True,
    )


def get_existing_flood_geojson(product_id, output_file_path="./output/"):
    """
    Getting a saved GFM flood geojson in an output folder of GFM files. Merge in one feature group if multiple.
    """
    index_df = pd.read_csv(output_file_path + "index.csv")
    geojson_path = index_df[index_df["product"] == product_id].geojson_path.values[0]

    with open(geojson_path, "r") as f:
        geojson_data = json.load(f)

    return geojson_data


def create_zipfile_buffer_from_geojsons(selected_geojsons):
    # Create an in-memory zip file
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for i, geojson in enumerate(selected_geojsons, start=1):
            geojson_str = json.dumps(geojson)  # Convert GeoJSON to string
            file_name = f"geojson_{i}.geojson"
            zipf.writestr(file_name, geojson_str)

    # Move the buffer cursor to the beginning so it can be read
    zip_buffer.seek(0)

    return zip_buffer
