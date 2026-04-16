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

## 3. 로컬 LLM 환경 (Local LLM Environment)

* **LLM 엔진 (서버):** Ollama (Windows 최신 버전, `v0.1.30` 이상 권장)
* **구동 모델 (Models):**
    1.  `llama3.1` (8B 파라미터, 4-bit 양자화) - Main Agent용 권장
    2.  `phi3:mini` (3.8B 파라미터, 4-bit 양자화) - 속도 최적화 및 테스트용

## 4. 파이썬 주요 의존성 패키지 (Python Dependencies)

`requirements.txt`에 포함되어야 할 핵심 패키지 및 권장 버전입니다.

| 패키지명 | 권장 버전 | 용도 |
| :--- | :--- | :--- |
| `openai` | `>= 1.14.0` | Ollama 로컬 API(`localhost:11434`) 통신 및 메인 에이전트 제어용 클라이언트 |
| `requests` | `>= 2.31.0` | SerpApi(Google Flights) REST API 호출 및 데이터 수집 |
| `python-dotenv` | `>= 1.0.1` | `.env` 파일을 통한 SerpApi Key 및 Telegram Token 등 환경변수 안전 관리 |
| `schedule` | `>= 1.2.1` | (선택) 파이썬 내부에서 매일 특정 시간에 스크립트를 실행하기 위한 스케줄러 |
| `pydantic` | `>= 2.6.0` | (선택) 에이전트 간 주고받는 JSON 데이터 구조 검증 및 파싱 |

## 5. 외부 연동 서비스 (External Services & APIs)

* **항공권 데이터 API:** SerpApi (Google Flights Engine)
    * *버전/규격:* REST API (최신 Endpoint 사용)
    * *응답 포맷:* JSON
* **알림 시스템 API:** Telegram Bot API
    * *버전:* HTTP-based API

## 6. 개발 도구 (Development Tools)

* **IDE (통합 개발 환경):** VS Code (Visual Studio Code) 권장
    * *필수 확장 프로그램:* Python, Pylance, Jupyter (필요시)
* **버전 관리:** Git

## 7. 실행 주의사항

* `openai` 라이브러리를 사용하되, 외부 클라우드로 데이터가 전송되지 않도록 코드 내 초기화 구문에서 `base_url='http://localhost:11434/v1'` 설정이 반드시 유지되어야 합니다.
* 가상환경(Virtual Environment) 세팅: 프로젝트 디렉토리 내에서 `python -m venv venv`를 통해 독립된 환경을 구성한 후 패키지를 설치해야 시스템 파이썬 환경과의 충돌을 방지할 수 있습니다.
