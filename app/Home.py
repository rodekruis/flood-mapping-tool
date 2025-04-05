"""Home page for Streamlit app."""

import streamlit as st
from src.config_parameters import params
from src.gfm import GFMHandler

# Page configuration
st.set_page_config(layout="wide", page_title=params["browser_title"])

from src.utils import (
    add_about,
    set_home_page_style,
    toggle_menu_button,
)

# If app is deployed hide menu button
toggle_menu_button()

# Initialize GFMHandler if not already in session state
if "gfm_handler" not in st.session_state:
    st.session_state["gfm_handler"] = GFMHandler()

# Create sidebar
add_about()

# Set page style
set_home_page_style()

# Page title
st.markdown("# Home")

# First section
st.markdown("## Introduction")
st.markdown("TODO: new introduction")

# Second section
st.markdown("## How to use the tool")
st.markdown("TODO: new how to use the tool")
