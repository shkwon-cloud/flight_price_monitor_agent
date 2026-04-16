"""
SerpApi Google Flights API 연동 모듈.

PRD FR-1 구현: Two-Phase 탐색 알고리즘
  Phase 1: 편도 선행 탐색 → 최저가 출발일 Top 3 추출
  Phase 2: Top 3 출발일에 대해 짝수일(4~14일) 체류 왕복 탐색

PRD FR-2 구현: 역대 최저가 및 타겟 가격 산출
  price_insights에서 역대 최저가 추출 → 최저가 × 1.2 = 알림 타겟 가격
"""

import time
import random
import json
import requests
from datetime import datetime, timedelta
from typing import Optional

from flight_agent.config import (
    DEPARTURE_ID, ARRIVAL_ID,
    SEARCH_DAYS, TOP_N_CHEAPEST, STAY_DURATIONS,
    PRICE_THRESHOLD_RATIO,
    SERPAPI_API_KEY, SERPAPI_BASE_URL,
    API_DELAY_MIN, API_DELAY_MAX, API_MAX_RETRIES, API_TIMEOUT,
    CURRENCY, GL, HL,
)


# ============================================================
# SerpApi 저수준 호출 함수 (Internal)
# ============================================================

def _call_serpapi(params: dict) -> dict:
    """
    SerpApi를 호출합니다. Rate Limit 방어(Sleep/Jitter)와 재시도 로직을 포함합니다.

    Args:
        params: SerpApi 요청 파라미터 딕셔너리

    Returns:
        API 응답 JSON 딕셔너리. 에러 시 {"status": "error", "message": "..."} 반환.
    """
    params["api_key"] = SERPAPI_API_KEY
    params["engine"] = "google_flights"

    for attempt in range(API_MAX_RETRIES):
        try:
            # NFR: Rate Limit 방어 - 호출 간 의도적 지연 (0.5~1.0초)
            time.sleep(random.uniform(API_DELAY_MIN, API_DELAY_MAX))

            response = requests.get(
                SERPAPI_BASE_URL, params=params, timeout=API_TIMEOUT
            )

            # 429 Too Many Requests - 백오프 후 재시도
            if response.status_code == 429:
                wait_time = (attempt + 1) * 2
                print(f"    ⏳ Rate limit 도달. {wait_time}초 대기 후 재시도... ({attempt+1}/{API_MAX_RETRIES})")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            print(f"    ⏳ 타임아웃. 재시도... ({attempt+1}/{API_MAX_RETRIES})")
            if attempt == API_MAX_RETRIES - 1:
                return {"status": "error", "message": f"API 타임아웃 ({API_TIMEOUT}초 초과)"}

        except requests.exceptions.RequestException as e:
            print(f"    ⚠ 요청 에러: {e}")
            if attempt == API_MAX_RETRIES - 1:
                return {"status": "error", "message": str(e)}

    return {"status": "error", "message": "최대 재시도 횟수 초과"}


def _search_oneway(departure_id: str, arrival_id: str, date: str) -> dict:
    """특정 날짜의 편도 항공권을 검색합니다."""
    params = {
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": date,
        "type": "2",       # One way
        "currency": CURRENCY,
        "gl": GL,
        "hl": HL,
        "adults": "1",
    }
    return _call_serpapi(params)


def _search_roundtrip(departure_id: str, arrival_id: str,
                      outbound_date: str, return_date: str) -> dict:
    """특정 출발일/귀국일의 왕복 항공편을 검색합니다."""
    params = {
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "type": "1",       # Round trip
        "currency": CURRENCY,
        "gl": GL,
        "hl": HL,
        "adults": "1",
    }
    return _call_serpapi(params)


# ============================================================
# 데이터 추출 유틸리티 (Internal)
# ============================================================

def _extract_lowest_price(api_response: dict) -> Optional[int]:
    """API 응답에서 최저가를 추출합니다."""
    best_flights = api_response.get("best_flights", [])
    other_flights = api_response.get("other_flights", [])
    all_flights = best_flights + other_flights

    prices = []
    for flight in all_flights:
        price = flight.get("price")
        if price is not None:
            prices.append(int(price))

    return min(prices) if prices else None


def _extract_flight_details(flight_data: dict) -> dict:
    """항공편 상세 정보를 추출합니다."""
    details = {}
    flights = flight_data.get("flights", [])

    if flights:
        first_leg = flights[0]
        details["airline"] = first_leg.get("airline", "Unknown")
        details["flight_number"] = first_leg.get("flight_number", "")

        dep_airport = first_leg.get("departure_airport", {})
        details["departure_airport"] = dep_airport.get("name", "")
        details["departure_time"] = dep_airport.get("time", "")

        arr_airport = first_leg.get("arrival_airport", {})
        details["arrival_airport"] = arr_airport.get("name", "")
        details["arrival_time"] = arr_airport.get("time", "")

        details["duration"] = first_leg.get("duration", 0)
        details["stops"] = len(flights) - 1  # 경유 횟수

    details["booking_token"] = flight_data.get("departure_token", "")
    return details


def _extract_price_insights(api_response: dict) -> dict:
    """price_insights에서 역대 최저가 정보를 추출합니다. (FR-2)"""
    insights = api_response.get("price_insights", {})
    return {
        "lowest_price": insights.get("lowest_price"),
        "price_level": insights.get("price_level"),
        "typical_price_range": insights.get("typical_price_range", []),
    }


# ============================================================
# 메인 Tool 함수 (ADK Agent가 호출)
# ============================================================

def search_and_analyze_flights() -> dict:
    """
    인천(ICN)-다낭(DAD) 노선의 최저가 항공권을 검색하고 분석합니다.

    Two-Phase 알고리즘을 사용합니다:
      Phase 1: 향후 30일간 편도 최저가를 검색하여 가장 저렴한 출발일 Top 3를 추출합니다.
      Phase 2: Top 3 출발일에 대해 4일~14일(짝수) 체류하는 왕복 항공권을 검색합니다.

    검색 완료 후 역대 최저가 대비 타겟 가격(최저가 × 1.2)을 산출하고,
    타겟 가격 이하인 거래를 필터링하여 반환합니다.

    Returns:
        검색 결과, 가격 분석, 추천 거래 정보를 담은 딕셔너리
    """
    today = datetime.now()
    results = {
        "status": "success",
        "search_date": today.strftime("%Y-%m-%d"),
        "route": f"{DEPARTURE_ID} → {ARRIVAL_ID}",
        "phase1_results": [],
        "phase2_results": [],
        "historical_lowest_price": None,
        "target_price": None,
        "deals_found": [],
        "best_deal": None,
        "api_calls_count": 0,
    }

    # ===== PHASE 1: 편도 선행 탐색 =====
    print(f"\n{'='*60}")
    print(f"✈  [Phase 1] 편도 탐색 시작: {DEPARTURE_ID} → {ARRIVAL_ID}")
    print(f"   탐색 기간: {today.strftime('%Y-%m-%d')} ~ "
          f"{(today + timedelta(days=SEARCH_DAYS-1)).strftime('%Y-%m-%d')} ({SEARCH_DAYS}일)")
    print(f"{'='*60}")

    daily_prices = []

    for day_offset in range(SEARCH_DAYS):
        search_date = (today + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        print(f"  [{day_offset+1:2d}/{SEARCH_DAYS}] {search_date} 편도 검색 중...", end=" ")

        response = _search_oneway(DEPARTURE_ID, ARRIVAL_ID, search_date)
        results["api_calls_count"] += 1

        # 에러 처리 (NFR: 스크립트 중단 방지)
        if response.get("status") == "error":
            print(f"⚠ {response.get('message', 'Unknown error')}")
            continue

        # 최저가 추출
        lowest_price = _extract_lowest_price(response)
        if lowest_price is not None:
            daily_prices.append({"date": search_date, "price": lowest_price})
            print(f"✓ {lowest_price:,}원")
        else:
            print("✗ 항공편 없음")

        # price_insights에서 역대 최저가 수집 (첫 번째 유효 응답에서)
        if results["historical_lowest_price"] is None:
            insights = _extract_price_insights(response)
            if insights["lowest_price"]:
                results["historical_lowest_price"] = insights["lowest_price"]

    # Top N 최저가 출발일 추출
    daily_prices.sort(key=lambda x: x["price"])
    top_dates = daily_prices[:TOP_N_CHEAPEST]
    results["phase1_results"] = daily_prices

    if not top_dates:
        results["status"] = "no_flights"
        results["message"] = "Phase 1에서 항공편을 찾을 수 없습니다."
        print("\n  ❌ 탐색 가능한 항공편이 없습니다.")
        return results

    print(f"\n  🏆 Top {TOP_N_CHEAPEST} 최저가 출발일:")
    for i, item in enumerate(top_dates, 1):
        print(f"     {i}. {item['date']} — {item['price']:,}원")

    # ===== PHASE 2: 왕복 결합 탐색 =====
    total_phase2 = len(top_dates) * len(STAY_DURATIONS)
    print(f"\n{'='*60}")
    print(f"✈  [Phase 2] 왕복 탐색 시작")
    print(f"   대상 출발일: {[d['date'] for d in top_dates]}")
    print(f"   체류 기간: {STAY_DURATIONS}일 (총 {total_phase2}회 검색)")
    print(f"{'='*60}")

    all_roundtrip_deals = []
    search_count = 0

    for date_info in top_dates:
        outbound_date = date_info["date"]
        outbound_dt = datetime.strptime(outbound_date, "%Y-%m-%d")

        for stay in STAY_DURATIONS:
            search_count += 1
            return_dt = outbound_dt + timedelta(days=stay)
            return_date = return_dt.strftime("%Y-%m-%d")

            print(f"  [{search_count:2d}/{total_phase2}] "
                  f"{outbound_date} → {return_date} ({stay}일 체류)...", end=" ")

            response = _search_roundtrip(
                DEPARTURE_ID, ARRIVAL_ID, outbound_date, return_date
            )
            results["api_calls_count"] += 1

            # 에러 처리
            if response.get("status") == "error":
                print(f"⚠ {response.get('message', 'Unknown error')}")
                continue

            # 최저가 추출
            lowest_price = _extract_lowest_price(response)
            if lowest_price is not None:
                deal = {
                    "outbound_date": outbound_date,
                    "return_date": return_date,
                    "stay_days": stay,
                    "price": lowest_price,
                }

                # 항공편 상세 정보 추출
                best_flights = response.get("best_flights", [])
                if best_flights:
                    deal["details"] = _extract_flight_details(best_flights[0])

                all_roundtrip_deals.append(deal)
                print(f"✓ {lowest_price:,}원")
            else:
                print("✗ 항공편 없음")

            # 역대 최저가 보완 수집
            if results["historical_lowest_price"] is None:
                insights = _extract_price_insights(response)
                if insights["lowest_price"]:
                    results["historical_lowest_price"] = insights["lowest_price"]

    results["phase2_results"] = all_roundtrip_deals

    # ===== 가격 분석 (FR-2) =====
    # 역대 최저가가 없으면 검색 결과에서 최저가를 기준으로 사용
    if results["historical_lowest_price"] is None and all_roundtrip_deals:
        cheapest = min(all_roundtrip_deals, key=lambda x: x["price"])
        results["historical_lowest_price"] = cheapest["price"]

    # 타겟 가격 산출: 역대 최저가 × 1.2
    if results["historical_lowest_price"] is not None:
        target_price = int(results["historical_lowest_price"] * PRICE_THRESHOLD_RATIO)
        results["target_price"] = target_price

        # 타겟 가격 이하 거래 필터링
        deals = [d for d in all_roundtrip_deals if d["price"] <= target_price]
        deals.sort(key=lambda x: x["price"])
        results["deals_found"] = deals

        if deals:
            results["best_deal"] = deals[0]

    # ===== 결과 요약 출력 =====
    print(f"\n{'='*60}")
    print(f"📊 [분석 결과 요약]")
    print(f"   노선: {results['route']}")
    if results["historical_lowest_price"]:
        print(f"   역대 최저가: {results['historical_lowest_price']:,}원")
    else:
        print(f"   역대 최저가: 정보 없음")
    if results["target_price"]:
        print(f"   타겟 가격 (최저가×{PRICE_THRESHOLD_RATIO}): {results['target_price']:,}원")
    print(f"   발견된 거래: {len(results['deals_found'])}건")
    print(f"   총 API 호출: {results['api_calls_count']}회")

    if results["best_deal"]:
        bd = results["best_deal"]
        print(f"\n   🎉 최적 거래 발견!")
        print(f"      출발: {bd['outbound_date']}")
        print(f"      귀국: {bd['return_date']} ({bd['stay_days']}일 체류)")
        print(f"      가격: {bd['price']:,}원")
        if "details" in bd:
            d = bd["details"]
            print(f"      항공사: {d.get('airline', 'N/A')}")
            stops = d.get('stops', 0)
            stops_text = "직항" if stops == 0 else f"{stops}회 경유"
            print(f"      경유: {stops_text}")
    else:
        print(f"\n   ℹ 타겟 가격 이하의 거래가 없습니다.")

    print(f"{'='*60}\n")

    return results
