"""
프로젝트 전역 설정값 관리 모듈.
PRD/TRD 기반 노선 정보, 탐색 파라미터, API 설정, LLM 설정을 정의합니다.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 노선 설정 (Route Configuration)
# ============================================================
DEPARTURE_ID = "ICN"   # 인천국제공항 (Incheon International Airport)
ARRIVAL_ID = "DAD"     # 다낭국제공항 (Da Nang International Airport)

# ============================================================
# 탐색 파라미터 (Search Parameters)
# ============================================================
SEARCH_DAYS = 3                           # Phase 1: 편도 탐색 기간 (일) ※ 간편시험용: 30→3
TOP_N_CHEAPEST = 3                        # Phase 1: 추출할 최저가 출발일 수
STAY_DURATIONS = [2]                      # Phase 2: 체류 기간 ※ 간편시험용: [4,6,8,10,12,14]→[3]

# ============================================================
# 가격 임계치 (Price Threshold)
# ============================================================
PRICE_THRESHOLD_RATIO = 1.2  # 알림 기준: 역대 최저가 × 1.2

# ============================================================
# SerpApi 설정 (API Configuration)
# ============================================================
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
SERPAPI_BASE_URL = "https://serpapi.com/search"
API_DELAY_MIN = 0.5    # API 호출 간 최소 대기 시간 (초)
API_DELAY_MAX = 1.0    # API 호출 간 최대 대기 시간 (초)
API_MAX_RETRIES = 3    # 429 에러 시 최대 재시도 횟수
API_TIMEOUT = 30       # API 응답 타임아웃 (초)

# ============================================================
# 현지화 설정 (Localization)
# ============================================================
CURRENCY = "KRW"   # 통화: 한국 원
GL = "kr"          # 국가: 한국
HL = "ko"          # 언어: 한국어

# ============================================================
# LLM 설정 (Local LLM Configuration)
# ============================================================
OLLAMA_MODEL = "ollama/llama3.1"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
