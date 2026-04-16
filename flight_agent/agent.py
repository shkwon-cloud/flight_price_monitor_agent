"""
ADK 에이전트 정의 모듈.

PRD Section 3 구현: Sub-agent 위임 (Handoff) 패턴
  - Main Agent (오케스트레이터): 전체 워크플로우 지휘, 알림 발송 여부 판단
  - Sub-Agent #1 (데이터 수집/분석): SerpApi 호출, 가격 분석, JSON 결과 반환
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from flight_agent.config import OLLAMA_MODEL, OLLAMA_HOST
from flight_agent.tools.flight_search import search_and_analyze_flights
from flight_agent.tools.price_analyzer import format_alert_message


# ============================================================
# LLM 모델 설정
# ============================================================
llm_model = LiteLlm(
    model=OLLAMA_MODEL,
    api_base=OLLAMA_HOST,
)


# ============================================================
# Sub-Agent #1: 데이터 수집 및 분석 전담
# ============================================================
data_collector_agent = Agent(
    name="flight_data_collector",
    model=llm_model,
    description="항공권 데이터를 수집하고 가격을 분석하는 전문 에이전트입니다.",
    instruction="""당신은 항공권 데이터 수집 및 분석 전문 에이전트입니다.

당신의 역할:
1. search_and_analyze_flights 도구를 호출하여 ICN(인천)→DAD(다낭) 노선의 항공권 데이터를 수집합니다.
2. 도구가 반환한 결과를 그대로 상위 에이전트에게 전달합니다.

중요 규칙:
- 반드시 search_and_analyze_flights 도구를 호출하세요.
- 도구의 결과를 임의로 수정하거나 가격을 추측하지 마세요.
- 도구가 반환한 JSON 결과를 그대로 보고하세요.
""",
    tools=[search_and_analyze_flights],
)


# ============================================================
# Main Agent: 오케스트레이터
# ============================================================
main_agent = Agent(
    name="flight_monitor_main",
    model=llm_model,
    description="항공권 모니터링 오케스트레이터 에이전트입니다.",
    instruction="""당신은 최적가 항공권 모니터링 오케스트레이터입니다.

당신의 역할:
1. 사용자가 항공권 검색을 요청하면, flight_data_collector 에이전트에게 데이터 수집을 위임하세요 (이때 transfer_to_flight_data_collector 도구를 사용하세요).
2. flight_data_collector가 반환한 결과를 바탕으로 텍스트로 분석 결과를 작성하세요. (주의: 절대로 다른 분석 목적의 가상의 도구를 호출하려고 시도하지 마세요. 도구를 쓰지 말고 바로 텍스트로 응답해야 합니다.)
3. 결과에 deals_found(발견된 거래)가 있으면 사용자에게 좋은 소식을 알려주세요.
4. deals_found가 비어있으면 현재는 좋은 거래가 없다고 알려주세요.

알림 메시지에 반드시 포함할 정보:
- 최적 출발일 / 귀국일
- 여행 기간 (체류 일수)
- 항공사
- 세금 포함 최종 가격 (KRW)
- 역대 최저가 대비 현재 가격 수준

중요 규칙:
- 가격을 추측하거나 만들어내지 마세요. 반드시 도구 결과의 실제 데이터만 사용하세요.
- 한국어로 응답하세요.
""",
    sub_agents=[data_collector_agent],
)
