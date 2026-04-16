"""
최적가 항공권 모니터링 AI 에이전트 - 엔트리포인트

실행 방법:
    python main.py

환경 요구사항:
    1. Ollama가 실행 중이어야 합니다 (ollama serve)
    2. .env 파일에 SERPAPI_API_KEY가 설정되어야 합니다
"""

import sys
import asyncio
import warnings
import requests

warnings.filterwarnings("ignore", category=UserWarning)

from dotenv import load_dotenv
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from flight_agent.agent import main_agent
from flight_agent.config import OLLAMA_HOST, SERPAPI_API_KEY
from flight_agent.tools.price_analyzer import format_alert_message


def check_ollama_server() -> bool:
    """Ollama 서버가 실행 중인지 확인합니다."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            print(f"✅ Ollama 서버 연결 확인 ({OLLAMA_HOST})")
            print(f"   사용 가능 모델: {model_names}")
            return True
    except requests.exceptions.ConnectionError:
        pass

    print(f"❌ Ollama 서버에 연결할 수 없습니다 ({OLLAMA_HOST})")
    print(f"   → 'ollama serve' 명령으로 Ollama를 먼저 실행해주세요.")
    return False


def check_serpapi_key() -> bool:
    """SerpApi API Key가 설정되어 있는지 확인합니다."""
    if not SERPAPI_API_KEY or SERPAPI_API_KEY == "your_serpapi_key_here":
        print("❌ SerpApi API Key가 설정되지 않았습니다.")
        print("   → .env 파일에 SERPAPI_API_KEY를 설정해주세요.")
        return False

    print(f"✅ SerpApi API Key 확인 완료 (***{SERPAPI_API_KEY[-4:]})")
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

    # 에이전트에게 항공권 검색 요청
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=(
            "ICN(인천)에서 DAD(다낭)으로 가는 최저가 항공권을 검색해주세요. "
            "데이터를 수집한 후, 결과를 분석하여 좋은 거래(deals_found)가 있는지 알려주세요. "
            "이때, 별도의 분석 도구를 호출하지 말고 텍스트로만 요약해서 알려주세요."
        ))],
    )

    print(f"\n{'='*60}")
    print(f"🤖 항공권 모니터링 에이전트 실행 중...")
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
    print("  ✈  최적가 항공권 모니터링 AI 에이전트 (MVP)")
    print("  📍 노선: ICN (인천) → DAD (다낭)")
    print("=" * 60 + "\n")

    # 사전 조건 확인
    print("[환경 점검]")
    ollama_ok = check_ollama_server()
    serpapi_ok = check_serpapi_key()

    if not ollama_ok or not serpapi_ok:
        print("\n❌ 환경 점검 실패. 위의 안내에 따라 설정을 완료해주세요.")
        sys.exit(1)

    print(f"\n{'─'*60}")
    print("모든 환경 점검 통과. 에이전트를 시작합니다...")
    print(f"{'─'*60}")

    # 에이전트 실행
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
