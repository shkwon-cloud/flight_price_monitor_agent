항공권 가격 검색에 API를 사용하는 대신, Gemini LLM 모델에서 자연어로 질문하고, 출력을 JSON으로 받아서 처리하는 에이전트를 만들려고 합니다.  

1. 기본 모델 구성 (Model Configuration)
플랫폼: Google Cloud Vertex AI (B2B/Enterprise 환경)

모델명: gemini-1.5-flash

인증 방식: Google Cloud 서비스 계정(Service Account) 또는 ADC(Application Default Credentials)를 통한 인증 (API Key 방식 배제)

지역(Region): asia-northeast3 (서울)



응답은 반드시 사전에 정의된 JSON 스키마를 엄격히 준수할 것.


2. 데이터 출력 규격 (Output Schema)
응답 결과는 반드시 아래와 같은 JSON 형식이어야 함을 명시합니다.

JSON
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


💡 Antigravity 연동 시 개발자 참고 사항
Vertex AI SDK 사용: AI Studio의 google-generativeai 대신 google-cloud-aiplatform 라이브러리를 사용하도록 설정해야 합니다.

Project ID & Location: Vertex AI 호출을 위해 구글 클라우드 프로젝트 ID와 리전 정보를 환경 변수(PROJECT_ID, LOCATION)로 반드시 관리해야 합니다.