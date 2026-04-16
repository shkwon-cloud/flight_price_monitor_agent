# 기술 요구사항 정의서 (TRD)

**프로젝트명:** 최적가 항공권 모니터링 AI 에이전트 (MVP)
**문서 버전:** 1.0
**작성일자:** 2026년 4월 15일
**작성자:** 권순현 (Product Owner)

---

## 1. 시스템 실행 환경 (System Environment)

* **Operating System (OS):** Windows 10 또는 Windows 11 (64-bit)
* **CPU:** Intel Core i7-1165G7 (AVX-512 VNNI 지원 필수)
* **RAM:** 16GB (운영체제 제외 LLM 가용 메모리 최소 8GB 확보 권장)
* **GPU:** 불필요 (CPU 기반 추론)

## 2. 프로그래밍 언어 (Programming Language)

* **언어 및 추천 버전:** **Python 3.11.x (권장 버전: 3.11.8)**
    * *추천 사유:* 현재 AI 생태계(LangChain, OpenAI API Client, 각종 데이터 처리 라이브러리)에서 가장 호환성이 높고 안정적인 버전입니다. Python 3.12는 일부 구형 라이브러리와의 충돌이 발생할 수 있으며, 3.10 대비 3.11 버전이 실행 속도(약 10~60% 향상)와 메모리 관리 면에서 로컬 에이전트 구동에 더 유리합니다.

## 3. 클라우드 LLM 환경 (Cloud LLM Environment)

* **LLM 플랫폼:** Google Cloud Vertex AI
* **구동 모델:** `gemini-1.5-flash`
* **리전:** `asia-northeast3` (서울)
* **인증:** ADC (Application Default Credentials) 기반 접근. (로컬 개발 시 `gcloud auth application-default login` 사용 필수)

## 4. 파이썬 주요 의존성 패키지 (Python Dependencies)

`requirements.txt`에 포함되어야 할 핵심 패키지 및 권장 버전입니다.

| 패키지명 | 권장 버전 | 용도 |
| :--- | :--- | :--- |
| `google-cloud-aiplatform` | `>= 1.40.0` | Vertex AI 통신 및 메인/서브 에이전트 제어용 클라이언트 SDK |
| `python-dotenv` | `>= 1.0.1` | `.env` 파일을 통한 `PROJECT_ID`, `LOCATION` 및 Telegram Token 등 환경변수 관리 |
| `schedule` | `>= 1.2.1` | (선택) 파이썬 내부에서 매일 특정 시간에 스크립트를 실행하기 위한 스케줄러 |
| `pydantic` | `>= 2.6.0` | JSON 응답 규격(Structured Output) 정의 및 검증용 Pydantic 모델 |

## 5. 외부 연동 서비스 (External Services & APIs)

* **항공권 데이터 API:** 외부 API 사용 중단 (Gemini LLM 자체 추론으로 대체)
* **알림 시스템 API:** Telegram Bot API (HTTP-based API)

## 6. 개발 도구 (Development Tools)

* **IDE (통합 개발 환경):** VS Code (Visual Studio Code) 권장
* **클라우드 CLI:** Google Cloud CLI (`gcloud`) 필수
* **버전 관리:** Git

## 7. 실행 주의사항

* 기존의 `openai` 래퍼나 로컬 Ollama 환경 세팅 코드는 모두 정리해야 합니다.
* `PROJECT_ID`와 `LOCATION` 환경 변수가 누락되지 않도록 `.env` 작성에 유의합니다.
* 가상환경(Virtual Environment) 내부에서 의존성 패키지 설치(`pip install -r requirements.txt`)를 권장합니다.
