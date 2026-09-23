import datetime
import json
import logging
import os
from dotenv import load_dotenv
import urllib.parse
import urllib.request
import gzip

from directory import make_dir
from extract.extract_weather import extract_weather_data

def set_params():
    now  = datetime.datetime.now()
    base_date = now.strftime("%Y%m%d")

    test_data = {
        "base_time": "0600",
        "nx": "60",
        "ny": "127"
    }
   
    params = {
        "serviceKey": os.getenv("ServiceKey"),
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": test_data["base_time"],
        "nx": test_data["nx"],
        "ny": test_data["ny"]
    }

    return base_date, test_data, params

if __name__ == "__main__":

    ## Create necessary directories
    make_dir()

    ## Set parameters for the API request
    base_date, test_data, params = set_params()

    ### Extract weather data using the parameters
    extract_weather_data(base_date, test_data, params)