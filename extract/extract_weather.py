
import json
import logging
import os
from dotenv import load_dotenv
import urllib.parse
import urllib.request
import gzip

load_dotenv()

def extract_weather_data(base_date, test_data, params):

    query_string = urllib.parse.urlencode(params)
    full_url = f"{os.getenv('URL')}?{query_string}"

    try:
        logging.info(
            f"날씨 데이터 수집 시작 (날짜: {base_date}, 발표시각: {test_data['base_time']})"
        )
        # API 호출
        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                logging.info(f"[INFO] API 호출 성공: {response.status}")
                response_body = response.read().decode("utf-8")
                data = json.loads(response_body)

                #create reult file name
                file_path = f"data/raw/weather_{base_date}_{test_data['base_time']}.json.gz"

                # with open(file_path, "w", encoding="utf-8") as f:
                #     json.dump(data, f, ensure_ascii=False, indent=4)

                # Save the data as a gzipped JSON file
                # 131byte -> 121byte
                with gzip.open(file_path, "wt", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                logging.info(f"날씨 데이터 수집 성공 및 저장 완료: {file_path}")
                print(f"[SUCCESS] 수집 완료: {file_path}")
                return file_path
            else:
                logging.error(f"API 호출 실패: {response.status}")
                print(f"[ERROR] API 호출 실패: {response.status}")
    except Exception as e:
        logging.error(f"날씨 데이터 수집 중 오류 발생: {str(e)}")
        print(f"[ERROR] 날씨 데이터 수집 중 오류 발생: {str(e)}")
