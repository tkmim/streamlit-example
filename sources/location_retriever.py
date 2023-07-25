import base64
import json

import requests
import streamlit as st

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0',
}


def retrieve_options(name: str = "") -> dict:
    encoded_url = r"aHR0cHM6Ly9zZWFyY2gubWV0ZW9sb2dpeC5jb20veHgvYXV0b2NvbXBsZXRlL3VrL2RlP3E9"
    decoded_url = base64.b64decode(encoded_url).decode()
    url = f"{decoded_url}{name}"

    r = requests.get(url, headers=HEADERS)
    response = json.loads(r.text)
    if not isinstance(response, list):
        return {}
    return {f"{r['label']}, {r['country']}": r for r in response}


def location_widget():
    name = st.sidebar.text_input("Search", "Munic")
    if name:
        results = retrieve_options(name)
        if results:
            options = results.keys()
            option = st.sidebar.selectbox("Options", options)
            if option:
                location_name = results[option]["label"]
                location_id = results[option]["id"]
                return location_name, location_id
