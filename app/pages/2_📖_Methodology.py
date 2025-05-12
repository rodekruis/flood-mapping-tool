# """Documentation page for Streamlit app."""

import streamlit as st
from src.config_parameters import params
from src.utils import (
    add_about,
    set_doc_page_style,
    toggle_menu_button,
)

# Page configuration
st.set_page_config(layout="wide", page_title=params["browser_title"])

# If app is deployed hide menu button
toggle_menu_button()

# Create sidebar
add_about()

# Set page style
set_doc_page_style()

# Page title
st.markdown("# Documentation")

# First section
st.markdown("## Methodology")
st.markdown(
    """
    This tool does not produce its own forecasts; it leverages the flood forecasts created
    by the GloFAS Global Flood Monitoring tool and aims to make them conveniently accessible.

    The GFM products are generated using flood detection algorithms applied to Sentinel-1 satellite data,
    which captures radar imagery in all weather conditions. Sentinel-1 data,
    acquired in Interferometric Wide-swath mode and VV-polarization, is preprocessed into Analysis-Ready Data
    (ARD) with a 10x10 m pixel resolution. Three flood detection algorithms are then run in parallel on
    this ARD:

    - **HASARD (by LIST)**: Uses image comparison and statistical modeling to detect changes in
      flood-related signals.
    - **Alg2 (by DLR)**: Applies fuzzy logic and hierarchical thresholding to classify flooded areas.
    - **Alg3 (by TUW)**: Leverages long-term signal history and statistical modeling for efficient
      global flood mapping.

    Each algorithm independently classifies flooded pixels, and their results are
    combined into a consensus map. A pixel is marked as flooded if at least two of the three algorithms
    agree. This ensemble approach improves accuracy and ensures near-real-time flood monitoring globally.

    Detailed documentation on the methodology is available on the GloFAS
    website: https://global-flood.emergency.copernicus.eu/technical-information/glofas-gfm/

    The GloFAS documentation mentions 11 products that are published. The products used in this tool are 

    - **The observed flood extent**: these are the floods shown in red when analyzing floods on the
    "Flood Analysis" page
    - **The Sentinel-1 footprint**: this is the bounding box of the Sentinel-1 satellite image that contains the
    flood, shown in yellow when analyzing floods
    """
)


# Second section
st.markdown("## Radar imagery for flood detection")
st.markdown(
    """
    As described above, GFM uses Sentinel-1 data as the basis for its flood forecast.
    Sentinel-1 data is the result of measurements from a constellation of two
    satellites, assing over the same areas following the same orbit on average
    every 6 days. The figure below shows an overview of the Sentinel-1 observation
    plan, where pass directions and coverage frequencies are highlighted.
    More detailed documentation on Sentinel-1 can be found on the Copernicus website:
    https://sentiwiki.copernicus.eu/web/sentinel-1
    """,
    unsafe_allow_html=True,
)

# Add image satellite overview
st.image(
    "%s" % params["url_sentinel_img"],
    width=1000,
)
