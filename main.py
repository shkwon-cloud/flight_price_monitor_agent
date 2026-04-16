"""
최적가 항공권 모니터링 AI 에이전트 - 엔트리포인트

실행 방법:
    python main.py

환경 요구사항:
    1. gcloud auth application-default login 이 사전에 구동되어 있어야 합니다.
    2. .env 파일에 PROJECT_ID 가 설정되어야 합니다.
"""

import sys
import asyncio
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

from dotenv import load_dotenv
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from flight_agent.agent import main_agent
from flight_agent.config import PROJECT_ID, LOCATION


def check_gcp_env() -> bool:
    """GCP 환경 설정이 올바른지 점검합니다."""
    if not PROJECT_ID:
        print("❌ PROJECT_ID 가 설정되지 않았습니다.")
        print("   → .env 파일에 PROJECT_ID 및 LOCATION(선택)을 설정해주세요.")
        return False

    print(f"✅ GCP 환경 확인 완료 (Project: {PROJECT_ID}, Location: {LOCATION})")
    return True


async def run_agent():
    """에이전트를 실행합니다."""

    # Runner 생성
    session_service = InMemorySessionService()
    runner = Runner(
        agent=main_agent,
        app_name="flight_price_monitor",
        session_service=session_service,
    )

    # 세션 생성
    session = await session_service.create_session(
        app_name="flight_price_monitor",
        user_id="user1",
    )

    # 에이전트에게 항공권 검색 요청 (통합된 메시지)
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=(
            "ICN(인천)에서 DAD(다낭)으로 가는 저렴한 항공권을 찾아주세요. "
            "데이터를 수집한 후, 결과를 분석하여 표 포맷으로 요약 정리해주세요."
        ))],
    )

    print(f"\n{'='*60}")
    print(f"🤖 모델 추론 및 에이전트 실행 중...")
    print(f"{'='*60}")

    # 에이전트 실행 및 결과 수집
    final_response = ""

    async for event in runner.run_async(
        user_id="user1",
        session_id=session.id,
        new_message=user_message,
    ):
        # 최종 응답 수집
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_response += part.text

    # 결과 출력
    if final_response:
        print(f"\n{'='*60}")
        print(f"📋 에이전트 최종 응답:")
        print(f"{'='*60}")
        print(final_response)
    else:
        print("\n⚠ 에이전트로부터 응답을 받지 못했습니다.")

    print(f"\n{'='*60}")
    print(f"✅ 모니터링 완료")
    print(f"{'='*60}")


def main():
    """메인 실행 함수."""
    print("\n" + "=" * 60)
    print("  ✈  최적가 항공권 모니터링 AI 에이전트 (Vertex AI)")
    print("  📍 노선: ICN (인천) → DAD (다낭)")
    print("=" * 60 + "\n")

    # 사전 조건 확인
    print("[환경 점검]")
    gcp_ok = check_gcp_env()

    if not gcp_ok:
        print("\n❌ 환경 점검 실패. 위의 안내에 따라 설정을 완료해주세요.")
        sys.exit(1)

    print(f"\n{'─'*60}")
    print("모든 환경 점검 통과. 에이전트를 시작합니다...")
    print(f"{'─'*60}")

    # 에이전트 실행
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
