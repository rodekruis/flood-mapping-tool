import io

import pandas as pd
import streamlit as st
from huggingface_hub import HfApi


@st.cache_resource
def get_hf_api():
    return HfApi()


@st.cache_resource
def get_geojson_index_df():
    hf_api = get_hf_api()
    try:
        index_path = hf_api.hf_hub_download(
            repo_id="rodekruis/flood-mapping",
            filename="index.parquet",
            repo_type="dataset",
            force_download=True,
        )
        return pd.read_parquet(index_path)
    except Exception as e:
        st.warning(f"No index.parquet found on Hugging Face: {e}")
        return pd.DataFrame(columns=["aoi_id", "datetime", "product", "path_in_repo"])


def update_geojson_index_df(index_df: pd.DataFrame):
    hf_api = get_hf_api()

    write_buffer = io.BytesIO()
    index_df.to_parquet(write_buffer, index=False)

    hf_api.upload_file(
        path_or_fileobj=write_buffer,
        path_in_repo="index.parquet",
        repo_id="rodekruis/flood-mapping",
        repo_type="dataset",
    )
    get_geojson_index_df.clear()
