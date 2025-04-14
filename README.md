---
title: Flood Mapping Tool
emoji: 👀
colorFrom: yellow
colorTo: purple
sdk: streamlit
sdk_version: 1.44.1
app_file: app.py
pinned: false
license: gpl-3.0
---
# Flood Mapping Tool

## Installation & Running
### GFM account
To run the app you will need a (free) GFM account. To get one register at https://portal.gfm.eodc.eu/login . Once you have an account create a file `.env` with the content of `.env_template` where you will need to fill out your GFM username and password. The `.env` file will be gitignored.

### Python
Project is using python 3.12. Install requirements from `pyproject.toml` in your preferred way. We suggest using `uv`, see [here](https://docs.astral.sh/uv/getting-started/installation/) for installation instructions. Once installed your can run `uv sync` to create a `.venv` folder. Activate the `.venv` and then run the line below to run the app:

```
streamlit run app/Home.py
```

## Project
TODO: Add more complete documentation. 
