import os
from dotenv import load_dotenv

load_dotenv()


API_KEY = os.getenv("ServiceKey")


API_URL ="http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
BASE_TIME = "0500"
NX = "55"
NY = "127"
TIMEOUT = 10  # seconds
PAGE_NO = "1"
NUM_OF_ROWS = "1000"
