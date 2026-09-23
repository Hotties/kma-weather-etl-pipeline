weather_pipeline/
│
├── data/
│   ├── raw/          # API에서 받아온 순수 JSON 파일 (예: weather_2026-09-22.json)
│   └── processed/    # 정제 및 일별 집계가 끝난 CSV 파일
│
├── logs/
│   └── pipeline.log  # 수집 및 변환 과정의 로그 기록
│
├── main.py           # 전체 파이프라인 실행 스크립트
└── README.md         # 프로젝트 소개 및 실행법