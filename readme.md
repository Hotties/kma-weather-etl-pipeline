# KMA Weather ETL Pipeline

기상청 단기예보 API에서 날씨 예보를 수집하고, 필요한 항목을 정리해 CSV 파일로 저장하는 Python ETL 파이프라인입니다.

## 프로젝트 흐름

```text
기상청 단기예보 API
        │
        ▼
Extract: API 응답을 JSON 형식으로 받아 gzip 파일로 저장
        │
        ▼
Transform: TMP, REH, POP 항목을 예보 날짜·시각별로 정리
        │
        ▼
Load: 기존 CSV 데이터와 병합하여 날짜별 CSV 파일로 저장
```

## 프로젝트 구성

```text
.
├── config.py                       # API 및 요청 설정, 환경 변수에서 API 키 로드
├── directory.py                    # 데이터·로그 디렉터리 생성 및 로깅 설정
├── main.py                         # Extract → Transform → Load 실행 진입점
├── readme.md                       # 프로젝트 설명 및 실행 안내
├── data/
│   ├── raw/                        # 수집한 원본 API 응답
│   └── processed/                  # 변환한 예보 CSV 파일
├── extract/
│   └── extract_weather.py          # API 호출 및 gzip JSON 저장
├── transform/
│   └── transform_weather.py        # gzip JSON 읽기 및 예보 데이터 변환
└── load/
    └── load_weather.py             # 기존 데이터와 병합해 CSV 저장
```

실행하면 `directory.py`가 `data/raw/`, `data/processed/`, `logs/` 디렉터리를 생성합니다. `logs/pipeline.log`에는 실행 로그가 기록됩니다.

## 파일 설명

| 파일 | 설명 |
|---|---|
| `main.py` | 실행 날짜와 API 요청 파라미터를 설정하고 Extract, Transform, Load 순서로 호출합니다. 원본 파일 경로나 변환 결과가 없으면 오류를 기록하고 종료합니다. |
| `config.py` | `.env`에서 `ServiceKey`를 읽고 API URL, 발표 시각, 격자 좌표, 타임아웃, 페이지 번호, 요청 행 수를 정의합니다. |
| `directory.py` | 필요한 디렉터리를 만들고 `logs/pipeline.log` 파일 로깅을 설정합니다. |
| `extract/extract_weather.py` | API 요청을 보내 응답을 JSON으로 읽은 뒤 `data/raw/weather_<기준일>_<발표시각>.json.gz`에 저장합니다. |
| `transform/transform_weather.py` | gzip JSON의 응답 구조를 확인하고 예보 날짜·시각별로 기온, 습도, 강수확률을 모읍니다. |
| `load/load_weather.py` | `data/processed/weather_summary_<기준일>.csv`를 읽어 기존 날짜·시각 레코드를 유지하면서 새 레코드를 병합하고 정렬해 다시 저장합니다. |
| `.gitignore` | Python 캐시, 가상 환경, `.env`, 로그 등 Git에서 제외할 항목을 지정합니다. |

## 데이터 처리 특징

- **요청 기준**: 실행 시 시스템의 현재 날짜를 `YYYYMMDD`로 사용합니다. 발표 시각은 `0500`, 격자 좌표는 `NX=55`, `NY=127`로 설정되어 있습니다.
- **요청 설정**: 응답 형식은 JSON이며, 타임아웃은 10초, 페이지 번호는 1, 요청 행 수는 1000으로 설정되어 있습니다.
- **원본 저장**: 응답 JSON은 gzip으로 압축해 저장합니다. JSON을 들여쓰기 없이 간결하게 저장하고 한글 문자를 그대로 기록합니다.
- **변환 항목**: 기상청 카테고리 `TMP`는 `temperature`, `REH`는 `humidity`, `POP`은 `rain_probability`로 변환합니다. 날짜와 시각이 같은 값들을 한 레코드로 구성합니다.
- **CSV 저장**: CSV 열은 `fcstDate`, `fcstTime`, `temperature`, `humidity`, `rain_probability`입니다. 파일은 UTF-8 BOM을 포함하는 `utf-8-sig` 인코딩으로 기록되며 날짜·시각 순으로 정렬됩니다.
- **중복 처리**: 기존 CSV의 키는 예보 날짜와 시각의 조합입니다. 이미 존재하는 키는 기존 데이터를 유지하고, 새 키만 추가합니다.
- **로그와 오류**: 진행 상황은 콘솔에 출력하고 로그 파일에도 기록합니다. 필수 환경 변수나 입력이 없거나 응답 구조·파일 처리에 문제가 있으면 관련 함수에서 오류를 기록합니다.

## 실행 방법

### 1. 사전 준비

Python 환경에 `python-dotenv`를 설치합니다.

```powershell
python -m pip install python-dotenv
```

### 2. API 키 설정

프로젝트 루트에 `.env` 파일을 만들고 기상청 단기예보 API 서비스 키를 설정합니다.

```dotenv
ServiceKey=발급받은_서비스_키
```

`.env`는 Git에 커밋하지 마세요. 현재 `.gitignore`에서 제외하도록 설정되어 있습니다.

### 3. 파이프라인 실행

프로젝트 루트 디렉터리에서 실행합니다.

```powershell
python main.py
```

정상 실행 시 원본 데이터는 `data/raw/`, 변환 결과는 `data/processed/`에 저장됩니다.

## 출력 파일 예시

```text
data/
├── raw/
│   └── weather_20260929_0500.json.gz
└── processed/
    └── weather_summary_20260929.csv
```

처리 결과 CSV 예시:

```csv
fcstDate,fcstTime,temperature,humidity,rain_probability
20260929,0600,14,95,0
20260929,0700,14,95,0
```

## 추가하면 유용한 내용 제안

- 재현 가능한 설치를 위해 `requirements.txt`를 추가하고 Python 지원 버전과 설치 절차를 명시합니다.
- API 키 발급 절차, 서비스 키의 인코딩 여부, 자주 발생하는 API 오류 코드와 해결 방법을 문서화합니다.
- 발표 시각·격자 좌표·수집 날짜를 변경하는 방법과 현재 API의 요청 제한 및 페이지 처리 방식을 설명합니다.
- 자동 테스트 실행 방법과 대표적인 변환·중복 병합 테스트 사례를 추가합니다.
- 실제 실행 결과나 CSV 스키마를 더 자세히 설명하고, 예측 날짜가 기준 날짜와 다를 수 있다는 점을 안내합니다.
