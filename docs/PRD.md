# 제품 요구사항 정의서 (PRD)

**프로젝트명:** 최적가 항공권 모니터링 AI 에이전트 (MVP)
**문서 버전:** 1.0
**작성일자:** 2026년 4월 15일
**작성자:** 권순현 (Product Owner)
**수신:** Antigravity 개발팀

---

## 1. 프로젝트 개요 (Project Overview)

본 프로젝트는 사용자가 지정한 목적지의 항공권 가격을 매일 모니터링하고, 과거 데이터 기반의 역대 최저가와 비교하여 일정 비율(최저가 + 20%) 이내로 가격이 하락했을 때 자동으로 알림을 발송하는 **'AI 에이전트 기반 자동화 시스템'**을 구축하는 것을 목표로 합니다. 

초기 MVP(Minimum Viable Product) 단계에서는 복잡도를 낮추고 핵심 파이프라인 검증에 집중하기 위해 **'인천(ICN) - 다낭(DAD)'** 노선을 단일 타겟으로 설정합니다.

## 2. 시스템 아키텍처 및 개발 환경 (Architecture & Environment)

* **에이전트 프레임워크:** Google ADK (Agent Development Kit) 기반 Python 애플리케이션
* **LLM 플랫폼:** Google Cloud Vertex AI
* **타겟 LLM 모델:** `gemini-1.5-flash`
* **인증 방식:** Google Cloud 서비스 계정 (Service Account) 또는 ADC (Application Default Credentials)
* **리전 (Region):** `asia-northeast3` (서울)

## 3. 핵심 아키텍처 패턴: Sub-agent 위임 (Handoff)

에이전트는 역할을 분리하여 안정성과 효율성을 극대화합니다.

### 3.1. Main Agent (오케스트레이터)
* **역할:** 사용자 의도 파악, 전체 워크플로우 지휘, 알림 발송 여부 최종 판단.
* **동작 방식:** Sub-Agent #1에 목적지와 조건(예: 인천에서 다낭)을 전달하고 구체적으로 획득한 JSON 결과 데이터를 분석하여 알림을 발송합니다.

### 3.2. Sub-Agent #1 (데이터 검색 전담)
* **역할:** 항공권 외부 API 대신 Gemini LLM 모델에 직점 자연어로 질문하여 예측/검색 결과를 JSON 형태로 받아옵니다.
* **동작 방식:** 지정된 JSON 스키마를 엄격히 준수하도록 프롬프트/파라미터를 설정하여 LLM 응답을 파싱합니다.

## 4. 기능 요구사항 (Functional Requirements)

### FR-1. 자연어 기반 항공권 검색
* 기존의 API 호출 방식(Two-Phase 탐색 등)을 폐기하고, Gemini 1.5 Flash LLM을 통해 직접 항공권 정보를 예측 검색합니다.

### FR-2. JSON 구조화된 출력 (Structured Output)
* LLM의 응답은 반드시 아래와 같은 규격을 엄격하게 준수해야 합니다.
```json
{
  "search_parameters": {
    "origin": "string (IATA code)",
    "destination": "string (IATA code)",
    "departure_date": "YYYY-MM-DD",
    "target_price": "number"
  },
  "flight_results": [
    {
      "airline": "string",
      "price": "number (KRW)",
      "is_direct": "boolean",
      "is_target_met": "boolean"
    }
  ],
  "summary": "string (자연어 요약)"
}
```

### FR-3. Vertex AI 연동 설정
* `google-generativeai` 패키지 대신 `google-cloud-aiplatform` 라이브러리를 사용하도록 세팅합니다.
* 환경 변수(`PROJECT_ID`, `LOCATION`)를 통해 구글 클라우드 정보를 주입받아 인증을 수행합니다.

### FR-4. 매일 자동화 실행
* Windows 작업 스케줄러 또는 GitHub Actions/Cron 등을 활용하여, 개발된 Python 스크립트가 매일 지정된 시간에 1회 자동 실행되도록 구성해야 합니다.

### FR-5. 알림 전송 기능은 지금은 구현하지 않는다.
* 목표 가격 도달 시 사용자에게 즉각적인 알림을 발송하는 Tool을 연동합니다.
* **수단:** Telegram Bot API (MVP 우선 적용) 또는 Slack/Email 연동.
* **알림 내용:** 최적 출발/귀국 날짜, 여행 기간, 항공사, 세금 포함 최종 가격, 예약 링크.

## 5. 비기능 요구사항 (Non-Functional Requirements)

* **API Rate Limit 방어:** 다수 호출이 발생하는 Phase 2 검색 시, 봇 차단(`429 Error`)을 막기 위해 각 API 호출 사이에 의도적인 지연 시간(Sleep/Jitter, 최소 0.5초~1초)을 구현해야 합니다.
* **메모리 최적화:** RAM 16GB (가용 8GB) 환경이므로, LLM 구동 시 메모리 누수가 발생하지 않도록 컨텍스트 윈도우(Context Window)를 최소한으로 관리해야 합니다.
* **예외 처리:** 특정 날짜에 항공권이 없거나 API 응답 지연 시 스크립트가 중단되지 않고, 에이전트에게 자연어로 에러 상태(`status: error`)를 반환하도록 설계해야 합니다.

## 6. 마일스톤 및 산출물

* **산출물:** 1.  Google ADK 기반 Agent Python 소스 코드 일체
    2.  Ollama 설치 및 모델 구동이 포함된 로컬 환경 세팅 가이드 (README.md)
* **주요 마일스톤:** 계약 후 3일 이내에 단일 노선(다낭)에 대한 자동 모니터링 및 로컬 LLM 추론 결과를 확인하는 MVP 시연.
