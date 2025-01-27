"""Documentation page for Streamlit app."""

import streamlit as st
from PIL import Image
from src.config_parameters import params
from src.utils import (
    add_about,
    add_logo,
    set_doc_page_style,
    toggle_menu_button,
)

# Page configuration
st.set_page_config(layout="wide", page_title=params["browser_title"])

# If app is deployed hide menu button
toggle_menu_button()

# Create sidebar
add_logo("app/img/MA-logo.png")
add_about()

# Set page style
set_doc_page_style()

# Page title
st.markdown("# Documentation")

# First section
st.markdown("## Methodology")
st.markdown(
    "TODO: new documentation, only kept in Sentinel 1 section unchanged from the Mapaction tool"
)


# Second section
st.markdown("## Radar imagery for flood detection")
st.markdown(
    """
    While there are multiple change detections techniques for radar imagery,
    the one used by Sentinel-1 is one of the simplest. Active radar satellites
    produce active radiation directed at the land, and images are formed as a
    function of the time it takes for that radiation to reach back to the
    satellite. Because of this, radar systems are side-looking (otherwise
    radiation from multiple areas would reach back at the same time).  To be
    detected and imaged, radiation needs to be scattered back, but not all
    surfaces are equally able to scatter back, and that ability is also
    influenced by the radiation's wavelength (shorter wavelengths are better at
    detecting smaller objects, while longer wavelengths allow penetration,
    which is good for forest canopies for example, and biomass studies).
    Sentinel-1 satellites are C-band (~ 6 cm).<br><br>
    Water is characterised by a mirror-like reflection mechanism, meaning that
    no or very little radiation is scattered back to the satellite, so pixels
    on the image will appear very dark. This very simple change detection takes
    a "before" image, and looks for drops in intensity, dark spots, in the
    "after" image.<br><br>
    Sentinel-1 data is the result of measurements from a constellation of two
    satellites, assing over the same areas following the same orbit on average
    every 6 days. On Google Earth Engine, the processing level is Ground Range
    Detected (GRD), meaning that it has been detected, multi-looked and
    projected to ground range using an Earth ellipsoid model. GRD products
    report on intensity of radiation, but have lost the phase and amplitude
    information which is needed for other applications (interferometry for
    example). These satellites emits in different polarizations, and can
    acquire both single horizonal or vertical, or dual polarizations. Flood
    water is best detected by using VH (vertical transmit and horizontal
    receive), although VV (vertical transmit and vertical receive) can be
    effective to identify partially submerged features. This tool uses VH
    polarization. Figure 2 shows an overview of the Sentinel-1 observation
    plan, where pass directions and coverage frequencies are highlighted.
    """,
    unsafe_allow_html=True,
)

# Add image satellite overview
st.image(
    "%s" % params["url_sentinel_img"],
    width=1000,
)
st.markdown(
    """
        <p style="font-size:%s;">
            Figure 2. Overview of the Sentinel-1 observation plan (<a href=
            '%s'>source</a>).
        </p>
        """
    % (params["docs_caption_fontsize"], params["url_sentinel_img_location"]),
    unsafe_allow_html=True,
)
