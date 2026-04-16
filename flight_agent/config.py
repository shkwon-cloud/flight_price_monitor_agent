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
SEARCH_DAYS = 3                           # 탐색 기간
TOP_N_CHEAPEST = 3                        # 추출할 최저가 출발일 수
STAY_DURATIONS = [2]                      # 체류 기간 단위

# ============================================================
# 가격 임계치 (Price Threshold)
# ============================================================
PRICE_THRESHOLD_RATIO = 1.2  # 알림 기준: 역대 최저가 × 1.2

# ============================================================
# Google Cloud Vertex AI 설정 (API Configuration)
# ============================================================
PROJECT_ID = os.getenv("PROJECT_ID", "")
LOCATION = os.getenv("LOCATION", "us-central1")

os.environ["VERTEX_PROJECT"] = PROJECT_ID
os.environ["VERTEX_LOCATION"] = "us-central1"

#VERTEX_MODEL = "gemini-2.0-flash-lite-preview-02-05"
#ADK_LLM_MODEL = "vertex_ai/gemini-2.0-flash-lite-preview-02-05"
# 신규 프로젝트에서 제한 없이 접근 가능한 빠르고 안정적인 모델
VERTEX_MODEL = "gemini-2.5-flash-lite"
ADK_LLM_MODEL = "vertex_ai/gemini-2.5-flash-lite"

# ============================================================
# 현지화 설정 (Localization)
# ============================================================
CURRENCY = "KRW"   # 통화: 한국 원
GL = "kr"          # 국가: 한국
HL = "ko"          # 언어: 한국어
