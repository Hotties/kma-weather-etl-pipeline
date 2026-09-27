from datetime import datetime
import logging


from directory import make_dir
from extract.extract_weather import extract_weather_data
from transform.transform_weather import transform_weather_data
from load.load_weather import load_weather_data
from config import API_URL, API_KEY, BASE_TIME, NX, NY, TIMEOUT, PAGE_NO, NUM_OF_ROWS


# def set_params():
#     # now  = datetime.datetime.now()
#     # base_date = now.strftime("%Y%m%d")

#     base_date = "20210628"  # 테스트용 날짜 (실제 사용 시 현재 날짜로 변경 가능)
    
#     test_data = {
#         "base_time": "0500",
#         "nx": "55",
#         "ny": "127"
#     }
   
#     params = {
#         "serviceKey": os.getenv("ServiceKey"),
#         "pageNo": "1",
#         "numOfRows": "1000",
#         "dataType": "JSON",
#         "base_date": base_date,
#         "base_time": test_data["base_time"],
#         "nx": test_data["nx"],
#         "ny": test_data["ny"]
#     }

#     return base_date, test_data, params

def set_params():
    now = datetime.datetime.now()
    base_date = now.strftime("%Y%m%d")  # 현재 날짜를 YYYYMMDD 형식으로 가져오기

    params = {
        "serviceKey": API_KEY,
        "pageNo": PAGE_NO,
        "numOfRows": NUM_OF_ROWS,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": BASE_TIME,
        "nx": NX,
        "ny": NY
    }
    return base_date, BASE_TIME, params
if __name__ == "__main__":

    ## Create necessary directories
    make_dir()

    ## Set parameters for the API request
    base_date, base_time, params = set_params()

    ### Extract weather data using the parameters
    raw_file_path = extract_weather_data(base_date, base_time, params,timeout = TIMEOUT)

    ## if 문을 사용하여 none 값이 반환될 경우 프로그램 종료 처리
    if not raw_file_path:
        print("[ERROR] Raw file path is None. Exiting the program.")
        logging.error("[ERROR] Raw file path is None. Exiting the program.")
        exit(1)
    transformed_data = transform_weather_data(raw_file_path)
    if not transformed_data:
        print("[ERROR] Transformed data is None. Exiting the program.")
        logging.error("[ERROR] Transformed data is None. Exiting the program.")
        exit(1)
    load_weather_data(transformed_data)
