



from compression import gzip
import json
import logging
import os


def transform_weather_date(raw_file_path):

    ## transform the JSON date to Processed CSV
    ## no files in raw file path, return 
    if not raw_file_path or not os.path.exists(raw_file_path):
        logging.warning(f"Raw file path does not exist: {raw_file_path}")
        return

    ## open gzipped JSON file and read the data
    try:
        logging.info(f"Transforming weather data from: {raw_file_path}")
        with gzip.open(raw_file_path,"r", encoding="utf-8") as f:
            raw_data = json.load(f)

        items = raw_data["response"]["body"]["items"]["item"]

    except Exception as e:
        logging.error(f"Error reading raw weather data: {str(e)}")
        return