"""
가격 분석 유틸리티 모듈.

PRD FR-2 구현:
  - 역대 최저가 기반 타겟 가격 산출 (최저가 × 1.2)
  - 검색 결과 필터링 및 알림 메시지 생성
"""

from typing import Optional
from flight_agent.config import PRICE_THRESHOLD_RATIO


def calculate_target_price(historical_lowest: int) -> int:
    """
    역대 최저가를 기반으로 알림 타겟 가격을 산출합니다.

    Args:
        historical_lowest: 역대 최저가 (KRW)

    Returns:
        타겟 가격 (역대 최저가 × 1.2, 정수)
    """
    return int(historical_lowest * PRICE_THRESHOLD_RATIO)


def is_good_deal(price: int, target_price: int) -> bool:
    """
    현재 가격이 타겟 가격 이하인지 판단합니다.

    Args:
        price: 현재 항공편 가격 (KRW)
        target_price: 타겟 가격 (KRW)

    Returns:
        True if price <= target_price
    """
    return price <= target_price


def format_alert_message(analysis_result: dict) -> str:
    """
    분석 결과를 사용자 알림 메시지로 포맷합니다.
    (MVP: 콘솔 출력용. 추후 Telegram 연동 시 동일 포맷 사용 가능)

    Args:
        analysis_result: search_and_analyze_flights()의 반환값

    Returns:
        포맷된 알림 메시지 문자열
    """
    route = analysis_result.get("route", "N/A")
    search_date = analysis_result.get("search_date", "N/A")
    historical_lowest = analysis_result.get("historical_lowest_price")
    target_price = analysis_result.get("target_price")
    deals = analysis_result.get("deals_found", [])
    best_deal = analysis_result.get("best_deal")

    lines = []
    lines.append("=" * 50)
    lines.append("🛫 항공권 가격 알림")
    lines.append("=" * 50)
    lines.append(f"📅 검색일: {search_date}")
    lines.append(f"🛣  노선: {route}")
    lines.append("")

    if historical_lowest:
        lines.append(f"📉 역대 최저가: {historical_lowest:,}원")
    if target_price:
        lines.append(f"🎯 타겟 가격 (최저가×{PRICE_THRESHOLD_RATIO}): {target_price:,}원")
    lines.append("")

    if not deals:
        lines.append("ℹ 현재 타겟 가격 이하의 항공편이 없습니다.")
        lines.append("  다음 검색에서 가격이 내려갈 수 있으니 모니터링을 계속합니다.")
    else:
        lines.append(f"🎉 {len(deals)}건의 좋은 거래를 발견했습니다!")
        lines.append("")

        for i, deal in enumerate(deals[:5], 1):  # 상위 5건만 표시
            lines.append(f"  [{i}] {deal['outbound_date']} ~ {deal['return_date']} "
                        f"({deal['stay_days']}일 체류)")
            lines.append(f"      💰 가격: {deal['price']:,}원")

            if "details" in deal:
                d = deal["details"]
                airline = d.get("airline", "N/A")
                stops = d.get("stops", 0)
                stops_text = "직항" if stops == 0 else f"{stops}회 경유"
                lines.append(f"      ✈  {airline} ({stops_text})")
            lines.append("")

        if best_deal:
            lines.append("─" * 50)
            lines.append(f"⭐ 최적 추천: {best_deal['outbound_date']} ~ "
                        f"{best_deal['return_date']} ({best_deal['stay_days']}일)")
            lines.append(f"   {best_deal['price']:,}원")
            if target_price:
                savings = target_price - best_deal["price"]
                lines.append(f"   (타겟 대비 {savings:,}원 저렴)")

    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)
