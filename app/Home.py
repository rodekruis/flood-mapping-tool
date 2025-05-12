"""Home page for Streamlit app."""

import streamlit as st
from src.config_parameters import params

# Page configuration
st.set_page_config(layout="wide", page_title=params["browser_title"])

from src.utils import (  # noqa: E402
    add_about,
    set_home_page_style,
    toggle_menu_button,
)

# If app is deployed hide menu button
toggle_menu_button()

# Create sidebar
add_about()

# Set page style
set_home_page_style()

# Page title
st.markdown("# Home")

# First section
st.markdown("## Introduction")
st.markdown(
    """
    The goal of this Flood Mapping Tool is to provide visual insight into the extent of flood events.
    This tool does not produce its own forecasts; it leverages the flood forecasts created
    by the GloFAS Global Flood Monitoring (GFM) tool and aims to make them conveniently accessible.
    GFM uses satellite data from Sentinel-1 as the basis of its forecasts. More information on GFM
    and Sentinel-1 can be found on the Methodology page.

    How to use the Areas Of Interest and Flood Analysis pages is described below. The image below shows what
    you can expect a typical usage of the app to look like.
    """
)

st.image("app/img/application_example.png")

# Second section
st.markdown("## How to use the tool")
st.markdown("### Areas Of Interest")
st.markdown(
    """
    Because GFM internally works with Areas Of Interest (AOIs) our Flood Mapping Tool does as well.
    An AOI is basically the rectangular bounding box within which you will want to analyze floods.
    AOIs are shared among all users of the tool. If you create or delete an AOI, you will create or delete it
    for all users, so keep that in mind.

    There are three options on the Areas Of Interest page:
    - **See Areas**: You will see all AOIs that are already available in the tool, created by you or other users.
    When you hover over them you will see its name, which can be used to select it on the Flood Analysis page.
    - **Create New Area**: You can create a new AOI. To create a new area do the following:
        - Please first check whether an AOI that covers the area you are interested in exists already using "See Areas"
        - Find the location on the map either by zooming to it or by using the looking glass icon to search for a location and jump to it
        - Click the square icon, then hold down you mouse button and drag a rectangle shape on the screen
        - If you are unhappy with the shape, click the trash bin icon and then your shape to remove it and start again
        - If you are happy with the shape give it a (unique) name and hit the Save Area button
        - Saving can take up to minute, it is externally saved to GFM which takes some time 
    - **Delete Area**: Select an area by name and hit the Delete button to delete it. This will not delete
    the related flood products (see next section), only the AOI.
    """
)
st.markdown("### Flood Analysis")
st.markdown(
    """
    The flood analysis page is used to analyze the forecasted extent of floods. It is a forecast because the
    floods shown are the result of a forecasting model based on satellite data, as described on the Methodology page.
    They are forecasts of floods in the past though, it is the likely extent of a flood at the selected date and time.
    The tool does not forecast into the future.

    We will define a couple of terms you will see on this page first and then visually show how to use the page.

    - **AOI**: Area Of Interest as described in the previous section.
    - **Sentinel Footprint**: The bounding box of the Sentinel-1 satellite image. Floods are retrieved within the footprint.
    This will be a rectangle but it can be at an angle depending on the orbit path of the satellite. It is possible
    that a footprint only covers part of your AOI, so it is displayed to show you for which part of the AOI
    information is available.
    - **Product**: As described on the Methodology page this application shows flood extents forecasted by GFM.
    GFM offers their forecasts as products so we use the same terminology. A product contains the flood extents
    within a specific Sentinel Footprint, as described above, on a specific date and time, the time when the
    Sentinel measurements were taken.
    - **Product Time Group**: Sometimes your AOI will be large enough to have multiple products associated with it
    with timestamps just a couple seconds apart. This happens because the satellite first collected data for
    the first product and a few seconds later created the second product adjacent to it. In this case we group
    the products together and label them with the first timestamp of the group. In this case you can possibly see
    a more oddly shaped footprint, because it is multiple nearby footprints stitched together. 

    Using the page is more easily described visually. Below are some screenshots of the page with how-to-use
    descriptions in red.
    """
)

st.image("app/img/flood_analysis_doc1.png")
st.image("app/img/flood_analysis_doc2.png")
st.image("app/img/flood_analysis_doc3.png")
st.image("app/img/flood_analysis_doc4.png")
st.image("app/img/flood_analysis_doc5.png")
