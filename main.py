import os
from dotenv import load_dotenv

from directory import make_dir
from extract.extract_weather import extract_weather_data
from transform.tramsform_weather import transform_weather_data
from load.load_weather import load_weather_data


def set_params():
    # now  = datetime.datetime.now()
    # base_date = now.strftime("%Y%m%d")

    base_date = "20210628"  # 테스트용 날짜 (실제 사용 시 현재 날짜로 변경 가능)
    
    test_data = {
        "base_time": "0500",
        "nx": "55",
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
    raw_file_path = extract_weather_data(base_date, test_data, params)
    transformed_data = transform_weather_data(raw_file_path)
    load_weather_data(transformed_data)