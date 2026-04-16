"""
ADK 에이전트 정의 모듈.

PRD Section 3 구현: Sub-agent 위임 (Handoff) 패턴
  - Main Agent (오케스트레이터): 전체 워크플로우 지휘, 알림 발송 여부 판단
  - Sub-Agent #1 (데이터 수집/분석): Vertex AI 호출, 가격 분석, JSON 결과 반환
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from flight_agent.config import ADK_LLM_MODEL, PROJECT_ID, LOCATION
from flight_agent.tools.flight_search import search_and_analyze_flights
from flight_agent.tools.price_analyzer import format_alert_message


# ============================================================
# LLM 모델 설정 (Vertex AI 기반)
# ============================================================
llm_model = LiteLlm(
    model=ADK_LLM_MODEL,
    vertex_project=PROJECT_ID,
    vertex_location=LOCATION,
)


# ============================================================
# Sub-Agent #1: 데이터 수집 및 분석 전담
# ============================================================
data_collector_agent = Agent(
    name="flight_data_collector",
    model=llm_model,
    description="항공권 데이터를 클라우드 LLM을 사용해 가상으로 수집하고 분석하는 전문 에이전트입니다.",
    instruction="""당신은 항공권 데이터 예측 및 분석 에이전트입니다.

당신의 역할:
1. 반드시 search_and_analyze_flights 도구를 호출하여 ICN(인천)→DAD(다낭) 노선의 데이터를 수집합니다.
2. 반환받은 구조화된 JSON 결과를 상위 에이전트에게 그대로 반환합니다.

중요 규칙:
- 도구의 결과를 변조하거나 임ের로 가격을 만들지 마세요.
""",
    tools=[search_and_analyze_flights],
)
data_collector_agent.instruction += "\n- ★중요★: 모든 요약과 결과 전달은 영어 등 다른 언어를 쓰지 말고 반드시 한국어(Korean)로만 출력하세요."


# ============================================================
# Main Agent: 오케스트레이터
# ============================================================
main_agent = Agent(
    name="flight_monitor_main",
    model=llm_model,
    description="항공권 모니터링 오케스트레이터 에이전트입니다.",
    instruction="""당신은 최적가 항공권 모니터링 오케스트레이터입니다.

당신의 역할:
1. 사용자가 요청하면, [절대 직접 대답하지 말고] 반드시 'flight_data_collector' 에이전트에게 우선적으로 검색을 위임하세요.
2. 하위 에이전트가 반환한 JSON 데이터(search_parameters, flight_results, summary)를 기반으로만 사용자에게 보고할 텍스트를 작성하세요.
3. flight_results 배열에 목표 가격 요건을 만족하는 거래(is_target_met=True)가 있다면 여행자에게 좋은 소식을 알려주고 상세 정보를 표로 축약해 보여주세요.

알림 메시지에 포함할 정보:
- 출발지, 목적지, 추천 날짜
- 항공사 이름, 가격 현황 및 직항여부
- 응답 요약문(summary)

중요 규칙:
- ★명심하세요★: "잠시만 기다려주세요"나 "수집해오겠습니다" 같이 혼자 대화형 응답을 먼저 출력하면 절대 안 됩니다. 무조건 첫 번째 액션으로 하위 에이전트(flight_data_collector)를 호출하여 위임하세요!
- ★중요★: 최종 출력되는 보고서 작성 시 반드시 한국어(Korean)만 사용하세요! 표의 헤더와 내용 모두 영어가 아닌 한국어로 번역해서 출력해야 합니다.
- 데이터 수집 외의 목적으로 존재하지 않는 도구를 호출하려 시도하지 마세요.
""",
    sub_agents=[data_collector_agent],
)
