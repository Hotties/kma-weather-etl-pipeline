


import csv
import logging
import os

def load_weather_data(forecast_dict):
    processed_file_path = "data/processed/weather_summary.csv"
    file_exists = os.path.exists(processed_file_path)
    
    try:
        # Load: CSV 파일로 저장 (Append 모드로 누적)
        with open(
            processed_file_path, "a", newline="", encoding="utf-8-sig"
        ) as csv_file:
            fieldnames = [
            "fcstDate",
            "fcstTime",
            "temperature",
            "humidity",
            "rain_probability",
            ]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            ## Write header only if the file does not exist
            if not file_exists:
                writer.writeheader()

            ## writer.writerow()의 시행횟수를 줄이기 위해 수정
            ## 수정 전 시행 횟수 : n, 수정 후 : 1
            # count = 0
            # for key, data in forecast_dict.items():

            #     if data["temperature"] is not None:
            #         writer.writerow(data)
            #         count += 1   
            
            rows = [
                data for key, data in forecast_dict.items()
                if data["temperature"] is not None
            ]
            count = len(rows)
            writer.writerows(rows)

        logging.info(f"데이터 변환 및 적재 완료: {processed_file_path} ({count}건)")
        print(f"[SUCCESS] 변환 및 적재 완료: {processed_file_path} (총 {count}건)")    
    except Exception as e:
        logging.error(f"CSV 파일 열기 실패: {str(e)}")
        print(f"[ERROR] CSV 파일 열기 실패: {str(e)}")
        return
    return
