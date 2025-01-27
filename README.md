# Flood Mapping Tool

## Installation & Running
### GFM account
To run the app you will need a (free) GFM account. To get one register at https://portal.gfm.eodc.eu/login . Once you have an account create a file `.env` with the content of `.env_template` where you will need to fill out your GFM username and password. The `.env` file will be gitignored.

### Python
For now kept on python 3.10 like original Mapaction app. Create and activate your python3.10 venv in your preferred way, then:
```
pip install -r requirements.txt
streamlit run app/Home.py
```
For now its kept on python 3.10 like original Mapaction app and packages have not yet been updated.
Just create venv and pip install requirements. Then `streamlit run app/Home.py`

## Project
TODO: Add more complete documentation. 