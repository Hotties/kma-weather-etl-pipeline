# 날씨 데이터 파이프라인 최적화 가이드

이 문서는 현재 작업 트리의 날씨 데이터 ETL 파이프라인을 다시 검토한 결과입니다.
기존 제안 중 이미 반영된 내용과 아직 작업이 필요한 내용을 구분했습니다.

> 이 문서 갱신에서는 Python 소스 파일을 수정하지 않았습니다.

## 1. 현재 구조

```text
main.py
  ├─ directory.make_dir()
  ├─ extract.extract_weather_data()
  ├─ transform.transform_weather_data()
  └─ load.load_weather_data()
```

주요 데이터 흐름:

1. 기상청 API 요청
2. `data/raw`에 GZIP JSON 저장
3. 예보 항목을 날짜·시간별 딕셔너리로 변환
4. `data/processed/weather_summary.csv`에 누적 저장

## 2. 이미 반영된 최적화

### 2.1 표준 GZIP 모듈 사용

대상: `transform/tramsform_weather.py`

기존의 잘못된 import가 다음과 같이 변경되었습니다.

```python
import gzip
```

또한 GZIP 파일을 텍스트 모드로 읽고 있어 JSON 파싱 시 인코딩 오류가 발생하지 않는 방향으로 수정되었습니다.

```python
with gzip.open(raw_file_path, "rt", encoding="utf-8") as f:
```

### 2.2 카테고리 매핑 적용

대상: `transform/tramsform_weather.py`

`TMP`, `REH`, `POP`을 출력 필드에 매핑하는 딕셔너리가 추가되었습니다.

```python
category_mapping = {
    "TMP": "temperature",
    "REH": "humidity",
    "POP": "rain_probability"
}
```

기존의 여러 `if/elif` 조건보다 확장성이 좋아졌습니다. 이후 카테고리가 추가되면 매핑 테이블만 수정할 수 있습니다.

### 2.3 CSV 일괄 기록 적용

대상: `load/load_weather.py`

`writer.writerow()`를 반복 호출하던 방식이 `writer.writerows()` 방식으로 변경되었습니다.

```python
rows = [
    data for key, data in forecast_dict.items()
    if data["temperature"] is not None
]
writer.writerows(rows)
```

현재 데이터 규모에서는 차이가 작지만, 예보 지역이나 기간이 늘어나면 함수 호출 횟수를 줄이는 효과가 있습니다.

### 2.4 일부 불필요한 import 제거

다음 import는 제거되었습니다.

- `main.py`의 다수 미사용 표준 라이브러리 import
- `load/load_weather.py`의 `json`
- `load/load_weather.py`의 `transform_weather_data`

다만 `main.py`에는 아직 직접 사용하지 않는 `load_dotenv`가 남아 있으므로 아래 남은 항목에서 정리 대상으로 다룹니다.

## 3. 최우선으로 남은 개선 항목

### 3.1 ETL 단계 실패 전파 방지

대상:

- `main.py`
- `extract/extract_weather.py`
- `transform/tramsform_weather.py`
- `load/load_weather.py`

현재 Extract 또는 Transform이 오류를 처리한 뒤 `None`을 반환할 수 있습니다. 그러나 `main.py`는 다음 단계 실행 전에 반환값을 검증하지 않습니다.

```python
raw_file_path = extract_weather_data(base_date, test_data, params)
transformed_data = transform_weather_data(raw_file_path)
load_weather_data(transformed_data)
```

이 구조에서는 원래 오류 이후 다음과 같은 2차 오류가 발생할 수 있습니다.

```text
'NoneType' object has no attribute 'items'
```

#### 개선 방법 A: 단계별 결과 검증

- Extract 결과가 `None` 또는 빈 경로이면 Transform을 실행하지 않음
- Transform 결과가 `None` 또는 빈 딕셔너리이면 Load를 실행하지 않음
- 실패 시 로그를 남기고 프로그램을 종료

#### 개선 방법 B: 예외를 호출부까지 전달

각 단계에서 오류를 숨기고 `None`을 반환하는 대신, 의미 있는 예외를 발생시킵니다.

- `ExtractError`
- `TransformError`
- `LoadError`

`main.py`가 예외를 최종 처리하도록 하면 스케줄러나 배치 실행에서도 실패 상태를 정확히 알 수 있습니다.

### 3.2 API 환경변수 검증 및 타임아웃

대상: `extract/extract_weather.py`

현재 URL과 서비스 키를 검증하지 않고 문자열을 조합합니다.

```python
full_url = f"{os.getenv('URL')}?{query_string}"
```

환경변수가 없으면 다음과 같은 잘못된 요청이 생성될 수 있습니다.

```text
unknown url type: 'None?...'
```

또한 `urlopen()`에 타임아웃이 없습니다.

#### 개선 방법 A: 요청 전 설정값 검증

다음 값이 없거나 잘못된 경우 네트워크 요청 전에 즉시 실패시킵니다.

- `URL`
- `ServiceKey`
- `base_date`
- `base_time`
- `nx`, `ny`

#### 개선 방법 B: timeout과 제한적 재시도

```python
urllib.request.urlopen(req, timeout=30)
```

일시적인 네트워크 오류와 5xx 응답만 제한적으로 지수 백오프 재시도합니다. 403이나 잘못된 인증키는 재시도하지 않아야 합니다.

### 3.3 API 응답 구조 검증

대상: `extract/extract_weather.py`, `transform/tramsform_weather.py`

현재 Transform은 다음 구조가 항상 존재한다고 가정합니다.

```python
raw_data["response"]["body"]["items"]["item"]
```

하지만 HTTP 상태가 200이어도 API 내부 오류일 수 있습니다. 로그에서 `body` 키 누락 오류가 확인된 적도 있습니다.

#### 개선 방법 A: API 내부 응답 코드 확인

HTTP 상태와 함께 다음을 확인합니다.

- `resultCode`
- `resultMsg`
- `response.body`
- `items.item`

#### 개선 방법 B: 단계별 구조 검증 및 명시적 오류

필수 키가 누락되면 `KeyError`를 그대로 삼키지 말고, 응답 일부와 원인을 포함한 Transform 오류로 기록합니다. 빈 `item` 목록도 정상적인 빈 결과인지 API 오류인지 정책을 정해야 합니다.



==================================================================================================================================
## 4. 데이터 정합성과 운영 안정성 <현재 csv 파일을 확인 할 수 없어 수정 불가>

### 4.1 CSV 중복 적재 방지

대상: `load/load_weather.py`

현재 파일을 append 모드로 엽니다.

```python
with open(processed_file_path, "a", ...)
```

동일한 날짜와 발표 시각으로 여러 번 실행하면 같은 예보가 CSV에 반복해서 추가됩니다.

#### 개선 방법 A: 자연 키 기준 중복 제거

`(fcstDate, fcstTime)`를 기준으로 기존 행과 신규 행을 합친 뒤 중복을 제거합니다.

#### 개선 방법 B: 날짜별 파일 또는 데이터베이스 사용

다음과 같이 날짜별 파일을 만들 수 있습니다.

```text
weather_summary_20210628.csv
weather_summary_20260923.csv
```

데이터가 더 커지면 SQLite나 PostgreSQL에 `(fcstDate, fcstTime)` 고유 제약조건을 두는 방법이 적합합니다.

### 4.2 원자적 CSV 저장 <mariadb를 사용해서 해도 되나>

대상: `load/load_weather.py`

현재 CSV에 직접 append하므로 프로세스가 기록 중 종료되면 파일 일부만 추가될 수 있습니다.

#### 개선 방법 A: 임시 파일 작성 후 교체

새 내용을 임시 파일에 완전히 기록한 뒤 성공했을 때 기존 파일과 교체합니다.

#### 개선 방법 B: 데이터베이스 트랜잭션 사용

중복 방지까지 필요하다면 트랜잭션과 고유 제약조건을 제공하는 SQLite가 CSV보다 안전합니다.

## 5. 입력 및 설정 관리 개선

### 5.1 날짜 하드코딩 제거

대상: `main.py`

현재 날짜가 고정되어 있습니다.

```python
base_date = "20210628"
```

#### 개선 방법 A: 실행 시점의 날짜 사용

```python
datetime.datetime.now().strftime("%Y%m%d")
```

다만 기상청 발표 시각 기준으로 날짜가 바뀌는 경계 조건을 별도로 처리해야 합니다.

#### 개선 방법 B: CLI 인자 또는 환경변수 사용 <인자로 사용하는 방법 채택 수정예정>

CLI 예시:

```text
python main.py --date 20260923 --time 0600
```

환경변수 예시:

```text
WEATHER_BASE_DATE=20260923
WEATHER_BASE_TIME=0600
```

이 방법은 운영 실행과 과거 데이터 재처리를 모두 지원하기 쉽습니다.

### 5.2 설정과 경로 중앙화

현재 API 파라미터와 출력 경로가 여러 파일에 직접 작성되어 있습니다.

#### 개선 방법 A: 설정 객체 사용 <.env  파일에서 해야하나>

날짜, 발표 시각, 좌표, API 페이지 크기, timeout을 하나의 설정 객체나 설정 모듈에서 관리합니다.

#### 개선 방법 B: `pathlib.Path`와 프로젝트 기준 경로 사용

현재 상대 경로는 실행 위치가 프로젝트 루트가 아니면 다른 위치에 파일을 만들 수 있습니다. 프로젝트 기준 경로를 계산해 raw, processed, logs 경로를 일관되게 생성하는 것이 안전합니다.

## 6. 성능 및 저장 형식 개선

### 6.1 JSON 직렬화 비용 감소

대상: `extract/extract_weather.py`

현재 GZIP JSON을 다음처럼 들여쓰기하여 저장합니다.

```python
json.dump(data, f, ensure_ascii=False, indent=4)
```

#### 개선 방법 A: compact JSON 사용 <채택>

```python
json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
```

사람이 직접 읽을 필요가 없는 운영 raw 파일이라면 저장 크기와 직렬화 작업량을 줄일 수 있습니다.

#### 개선 방법 B: 원본 응답을 바로 보관

Extract 단계에서 구조 검증이 필요하지 않다면 API 응답 원문을 바로 GZIP으로 저장하고 Transform 단계에서 파싱합니다. 원본 재현성은 좋아지지만 Extract 단계의 응답 검증은 별도로 보완해야 합니다.

### 6.2 메모리 사용량 관리 <모르겟음>

현재 Extract는 응답 전체를 메모리에 읽고 JSON 객체로 변환한 후 다시 저장합니다.

#### 개선 방법 A: 현재 구조 유지 + 응답 크기 제한

`Content-Length`, 최대 응답 크기, `numOfRows`를 검증해 비정상적으로 큰 응답을 차단합니다.

#### 개선 방법 B: 대용량 데이터에 스트리밍 처리 적용

향후 응답이 매우 커질 경우 스트리밍 JSON 파서나 페이지 단위 처리를 검토합니다. 현재 데이터 규모에서는 복잡도를 늘리기보다 응답 크기 제한이 우선입니다.

## 7. 예외 처리와 로깅 개선

대상:

- `extract/extract_weather.py`
- `transform/tramsform_weather.py`
- `load/load_weather.py`

현재 세 모듈 모두 다음과 같이 넓은 범위의 예외를 잡습니다.

```python
except Exception as e:
```

또한 오류를 기록한 뒤 `None` 또는 단순 `return`으로 끝나므로 호출부가 실패를 알기 어렵습니다.

#### 개선 방법 A: 예외 유형별 처리

- `urllib.error.HTTPError`
- `urllib.error.URLError`
- `json.JSONDecodeError`
- `KeyError`
- `OSError`
- `csv.Error`

오류 종류에 따라 재시도, 로그 수준, 파이프라인 종료 여부를 다르게 처리합니다.

#### 개선 방법 B: traceback 기록

단순 문자열 로그 대신 다음과 같이 traceback을 기록합니다.

```python
logging.exception("날씨 데이터 변환 실패")
```

운영 장애의 실제 호출 경로를 추적하는 데 도움이 됩니다.

#### 개선 방법 C: 반환 계약 명확화 <호출부에서 검사 완료>

각 함수가 성공 시 반환하는 타입과 실패 시 동작을 명시합니다. `None` 반환을 사용할 경우 호출부에서 반드시 검사해야 하며, 더 명확한 방식은 실패 시 예외를 전달하는 것입니다.

## 8. 코드 품질 및 유지보수

### 8.1 남은 미사용 import 제거

대상: `main.py`

현재 `load_dotenv`는 `main.py`에서 직접 호출되지 않습니다. 실제 환경변수 로드는 `extract/extract_weather.py`의 모듈 import 시점에 수행되고 있습니다.

#### 개선 방법 A: `main.py`의 미사용 import 제거

정적 분석 경고를 줄이고 각 모듈의 책임을 명확하게 합니다.

#### 개선 방법 B: 환경변수 로딩 위치를 하나로 통일

환경변수 로딩을 진입점인 `main.py`에서 명시적으로 수행하고, 하위 모듈은 이미 로드된 설정만 사용하도록 구성할 수 있습니다.

### 8.2 파일명 오타 수정

현재 파일명:

```text
transform/tramsform_weather.py
```

권장 파일명:

```text
transform/transform_weather.py
```

변경할 경우 `main.py`와 관련 import 경로를 함께 수정해야 합니다. 이미 외부에서 해당 경로를 사용하고 있다면 호환성을 고려해야 합니다.

### 8.3 주석 처리된 구 코드 정리

대상:

- `main.py`
- `extract/extract_weather.py`
- `transform/tramsform_weather.py`
- `load/load_weather.py`

현재 이전 구현이 주석으로 남아 있습니다. 버전 관리는 Git이 담당하므로 최종 구현과 혼동될 수 있는 주석 처리 코드는 제거하는 것이 좋습니다.

## 9. 테스트 및 검증 추가

현재 저장소에는 테스트 파일이나 의존성 명세 파일이 확인되지 않았습니다.

### 최적화 방법 1: 단계별 단위 테스트

다음 케이스를 우선 테스트합니다.

- 정상 GZIP JSON 변환
- 일반 JSON 입력 처리 여부
- `response.body.items.item` 누락
- API 오류 응답
- `None` 입력
- 온도 값이 없는 항목 필터링
- CSV 헤더 생성
- 동일 데이터 재실행 시 중복 여부

### 최적화 방법 2: 통합 테스트

실제 API를 호출하지 않고 샘플 응답 파일을 사용해 다음 전체 흐름을 검증합니다.

```text
샘플 raw JSON → transform → CSV 저장
```

네트워크 테스트는 별도로 분리하고 API 키를 테스트 코드에 포함하지 않아야 합니다.

## 10. 권장 적용 순서

1. `main.py`에서 Extract와 Transform 결과 검증
2. API URL·서비스 키 검증 및 `timeout` 추가
3. API 내부 응답 코드와 JSON 구조 검증
4. 오류 발생 시 예외 전달 또는 명확한 실패 상태 반환
5. CSV 중복 적재 방지
6. 날짜·좌표·경로 설정 외부화
7. 예외 유형별 처리와 traceback 로깅 적용
8. CSV 원자적 저장 또는 SQLite 전환 검토
9. compact JSON 및 응답 크기 제한 적용
10. 테스트 추가
11. 미사용 import, 주석 처리된 구 코드, 파일명 오타 정리

현재 규모에서 가장 효과가 큰 항목은 단순 반복문 최적화가 아니라 다음 세 가지입니다.

- 실패 전파 방지
- 중복 적재 방지
- 네트워크 및 API 응답 검증
