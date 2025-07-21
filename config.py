# YouTube DeepSearch 설정 파일

# YouTube Data API v3 키 - 본인의 API 키로 변경해주세요
# https://console.developers.google.com/apis/credentials에서 발급받으세요
import os
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# API 관련 설정
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# 검색 관련 설정
MAX_RESULTS_PER_REQUEST = 50  # YouTube API 제한
DEFAULT_MAX_RESULTS = 100
MAX_TOTAL_RESULTS = 1000

# 영상 길이 기준 (초)
SHORTS_MAX_DURATION = 60  # 1분 이하는 쇼츠

# GUI 설정
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
ANALYSIS_WINDOW_WIDTH = 1000
ANALYSIS_WINDOW_HEIGHT = 700

# 컬럼 설정
MAIN_COLUMNS = ["Title", "Views", "Outlier Score", "Duration", "Subscribers", "Channel"]
MAIN_COLUMN_WIDTHS = [300, 100, 100, 80, 100, 150]

CHANNEL_COLUMNS = ["Title", "Views", "Outlier Score", "Duration", "Published"]
CHANNEL_COLUMN_WIDTHS = [300, 100, 100, 80, 150]

# 날짜 포맷
DATE_FORMAT = "%Y-%m-%d"
