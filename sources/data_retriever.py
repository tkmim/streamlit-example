import base64
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple, List

import numpy as np
import requests
import xarray
from bs4 import BeautifulSoup

from .cache import Cache
from .models import Models
from .variables import Variables

cache_file_path = Path("cache.pkl")

cache = Cache(cache_file_path)


def md5_hash(string: str) -> str:
    return hashlib.md5(string.encode()).hexdigest()


def get_data(location: int, variable: Variables, models: List[Models]) -> Tuple[bool, xarray.DataArray]:
    if len(models) > 1:
        return get_multi_model_data(location, variable, models)

    else:
        return get_model_data(location, variable, model=models[0])


def get_multi_model_data(location: int, variable: Variables, models: List[Models]) -> tuple[bool, xarray.DataArray]:
    all_data = [get_model_data(location, variable, model) for model in models]

    # data_arrays = [da.rename(key.name) for key, da in all_data.items()]
    data_arrays = [da for _, da in all_data]
    is_new = any([is_new for is_new, _ in all_data])

    concat: xarray.DataArray
    concat = xarray.concat(data_arrays, dim="member")

    # Rename members
    concat["member"] = range(concat["member"].size)
    concat = concat.interpolate_na(dim="time")
    return is_new, concat


def get_model_data(location: int, variable: Variables, model: Models) -> Tuple[bool, xarray.DataArray]:
    # Download webpage
    page = download_page(location, variable, model)

    # Compute hash
    page_hash = md5_hash(page.text + str(location) + str(variable) + str(model))
    if page_hash not in cache.raw_data:
        # Parse the webpage and obtain a dictionary
        parsed_data = parse_page(page)

        # Extract the relevant information as a data array
        dataArray = extract_variable_information(parsed_data)
        cache.raw_data[page_hash] = dataArray
        is_new = True
    else:
        dataArray = cache.raw_data[page_hash]
        is_new = False

    return is_new, dataArray


def download_page(location: int, variable: Variables, model: Models) -> requests.Response:
    encoded_url = b'aHR0cHM6Ly9tZXRlb2xvZ2l4LmNvbS91ay9hamF4L2Vuc2VtYmxl'
    URL = base64.b64decode(encoded_url).decode()

    REQUEST_PARAMS = {"city_id": str(location),
                      "model": model.value,
                      "model_view": "",
                      "param": variable.value,
                      }
    HEADERS = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0',

    }

    return requests.get(URL, headers=HEADERS, params=REQUEST_PARAMS)


def parse_page(page: requests.Response) -> dict:
    # Parse with BeautifulSoup
    soup = BeautifulSoup(page.content, 'html.parser')
    # Get script part
    try:
        script = soup.find(type="text/javascript").extract().string
    except AttributeError:
        raise AssertionError("Couldn't retrieve data")

    # Look for the variable that contains the data
    search_for = "var hcensemblelong_data = "

    # Split script in lines
    script_lines = script.split("\n")

    # Look for the first line
    start = [index for index, line in enumerate(script_lines) if line.count(search_for)][0]

    # Until the end
    data_lines = script_lines[start:]

    # FIXME: The data is in a json format but with some things that need fixing.
    #  A cleaner way of getting this done would be nice.
    data_in_json_format = "\n".join(data_lines)

    # Remove the variable declaration in the first line
    data_in_json_format = data_in_json_format.replace(search_for, "")
    # Make sure that only double commas are used
    data_in_json_format = data_in_json_format.replace("'", '"')
    # Remove last ;
    data_in_json_format = data_in_json_format.strip()[:-1]
    # Fix trailing comma problem. Spaces are important here.
    data_in_json_format = data_in_json_format.replace('                                "enabled": false,',
                                                      '                                "enabled": false')

    # After the fix, parse the data and convert it to a dictionary
    parsed_data = json.loads(data_in_json_format)

    return parsed_data


def extract_variable_information(parsed_data: dict) -> xarray.DataArray:
    # Extract the member data from the parsed data
    data_dictionary = {}
    for member in parsed_data:
        data_dictionary[member["name"]] = member["data"]

    # Get list of members
    members = list(data_dictionary.keys())

    def get_time_and_variable(member_data: dict) -> Tuple[list, list]:
        """
        Function to extract time and data values from data corresponding to a single member.
        :param member_data:
        :return:
        """
        time = [datetime.fromtimestamp(d[0] / 1000) for d in member_data]
        values = [d[1] for d in member_data]
        return time, values

    # Get the data shape to create an empty array
    times, var = get_time_and_variable(data_dictionary[members[-1]])

    data_shape = (len(members), len(times))
    data = np.empty(data_shape)
    data[:] = np.nan

    # Process all members to fill the array.
    for m_idx, member in enumerate(members):
        times, var = get_time_and_variable(data_dictionary[member])
        data[m_idx, :len(var)] = var

    # Convert numpy array to data array with the corresponding dimensions
    dataArray = xarray.DataArray(data, coords={"member": members, "time": times})

    return dataArray


def timedelta_as_hours(time: datetime) -> int:
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    td = time - today
    return int(td.days * 24 + td.seconds / 3600)
