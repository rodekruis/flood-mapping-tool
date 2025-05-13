"""Functions for the layout of the Streamlit app, including the sidebar."""

import json
import os
from typing import Literal

import streamlit as st

from src import hf_utils
from src.config_parameters import params


def get_aoi_id_from_selector_preview(all_aois, name):
    for aoi_id, aoi in all_aois.items():
        if aoi["name"] == name:
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
    st.sidebar.markdown("## Source Code")
    st.sidebar.markdown(
        f"""
        <p>
            <a href='{params["url_github_repo"]}'>
            Github Repo</a>
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("## Feedback")
    st.sidebar.markdown(
        """
        Were you able to find a useful flood map or experiencing a bug?
        Please leave any feedback through [this quick form](https://ee.ifrc.org/x/ZeCPlh7W).
        """
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


def get_existing_geojson(product_id, file_type: Literal["flood", "footprint"]):
    """
    Getting a saved GFM flood geojson in an output folder of GFM files. Merge in one feature group if multiple.
    """
    index_df = hf_utils.get_geojson_index_df()
    path_in_repo = index_df[index_df["product"] == product_id][
        f"{file_type}_geojson_path"
    ].values[0]

    hf_api = hf_utils.get_hf_api()
    subfolder, filename = path_in_repo.split("/")
    geojson_path = hf_api.hf_hub_download(
        repo_id="rodekruis/flood-mapping",
        filename=filename,
        repo_type="dataset",
        subfolder=subfolder,
    )

    with open(geojson_path, "r") as f:
        geojson_data = json.load(f)

    return geojson_data
