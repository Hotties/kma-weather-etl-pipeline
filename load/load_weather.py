


import csv
import logging
import os

def load_weather_data(forecast_dict, base_date):
    processed_file_path = f"data/processed/weather_summary_{base_date}.csv"
    file_exists = os.path.exists(processed_file_path)
    fieldnames = [
                    "fcstDate",
                    "fcstTime",
                    "temperature",
                    "humidity",
                    "rain_probability"
                ]

    ## 나중에 db 연결하여 load 구현
    ## 현재 같은 params를 사용하면 중복데이터 발생
    
    try:
        # # Load: CSV 파일로 저장 (Append 모드로 누적)
        # with open(
        #     processed_file_path, "a", newline="", encoding="utf-8-sig"
        # ) as csv_file:
        #     fieldnames = [
        #     "fcstDate",
        #     "fcstTime",
        #     "temperature",
        #     "humidity",
        #     "rain_probability",
        #     ]
        #     writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        #     ## Write header only if the file does not exist
        #     if not file_exists:
        #         writer.writeheader()

        #     ## writer.writerow()의 시행횟수를 줄이기 위해 수정
        #     ## 수정 전 시행 횟수 : n, 수정 후 : 1
        #     # count = 0
        #     # for key, data in forecast_dict.items():

        #     #     if data["temperature"] is not None:
        #     #         writer.writerow(data)
        #     #         count += 1   
            
        #     rows = [
        #         data for key, data in forecast_dict.items()
        #         if data["temperature"] is not None
        #     ]
        #     count = len(rows)
        #     writer.writerows(rows)

        ##날짜별로 파일을 나누어 저장
        existing_data = {}

        ## 기존 CSV 파일이 존재하면 데이터를 읽어와서 existing_data에 저장
        if file_exists:
            with open(processed_file_path, "r", newline="", encoding="utf-8-sig") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    key = (row["fcstDate"], row["fcstTime"])
                    existing_data[key] = row        
        print(f"[INFO] 기존 CSV 파일에서 {len(existing_data)}건의 데이터를 읽어왔습니다: {processed_file_path}")

        for record in forecast_dict.values():
            key = (record["fcstDate"], record["fcstTime"])
            if key not in existing_data:
                existing_data[key] = record
        print(f"[INFO] 새로운 데이터 {len(forecast_dict)}건을 기존 데이터와 병합했습니다.")
        
        
        with open(processed_file_path, "w", newline="", encoding = "utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for key in sorted(existing_data.keys()):
                writer.writerow(existing_data[key])
        count = len(existing_data.items())
        
        
        logging.info(f"데이터 변환 및 적재 완료: {processed_file_path} ({count}건)")
        print(f"[SUCCESS] 변환 및 적재 완료: {processed_file_path} (총 {count}건)")    
    except Exception as e:
        logging.error(f"CSV 파일 열기 실패: {str(e)}")
        print(f"[ERROR] CSV 파일 열기 실패: {str(e)}")
        return
    return
