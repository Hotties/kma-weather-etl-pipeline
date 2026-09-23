



import gzip
import json
import logging
import os


def transform_weather_data(raw_file_path):

    ## transform the JSON date to Processed CSV
    ## no files in raw file path, return 
    if not raw_file_path or not os.path.exists(raw_file_path):
        logging.warning(f"Raw file path does not exist: {raw_file_path}")
        return

    ## open gzipped JSON file and read the data
    try:
        logging.info(f"Transforming weather data from: {raw_file_path}")

        ## gzip을 열때 rt 모드로 열어야 함. (gzip.open()은 기본적으로 binary 모드로 열기 때문에, text 모드로 열어야 json.load()가 작동함)
        with gzip.open(raw_file_path,"rt", encoding="utf-8") as f:
            raw_data = json.load(f)

        items = raw_data["response"]["body"]["items"]["item"]

        forecast_dict = {}

        ## 사용할 category를 mapping하여 코드의 가독성을 높임
        category_mapping = {
            "TMP": "temperature",
            "REH": "humidity",
            "POP": "rain_probability"
        }

        for item in items:
            f_date = item.get("fcstDate")
            f_time = item.get("fcstTime")
            ##category = item.get("category")
            value = item.get("fcstValue")

            key = (f_date,f_time)

            if key not in forecast_dict:
                forecast_dict[key] = {
                    "fcstDate": f_date,
                    "fcstTime": f_time,
                    "temperature": None, ## 온도
                    "humidity": None, ## 습도
                    "rain_probability": None, ## 강수확률
                }

            # if category == "TMP":
            #     forecast_dict[key]["temperature"] = value
            # elif category == "REH":
            #     forecast_dict[key]["humidity"] = value
            # elif category == "POP":
            #     forecast_dict[key]["rain_probability"] = value 
            
            ## 조건문 사용 횟수 감소
            if item.get("category") in category_mapping:
                mapped_category = category_mapping[item.get("category")]
                forecast_dict[key][mapped_category] = value

        return forecast_dict
        
    except Exception as e:
        logging.error(f"Error reading raw weather data: {str(e)}")
        return