"""
Vertex AI Gemini 1.5 Flash 연동 모듈.

PRD FR-1, FR-2 구현: 
Vertex AI의 Structured Output 기능을 통해
자연어 항공권 검색을 수행하고, 지정된 JSON 스키마를 엄격히 준수하는 결과를 반환합니다.
"""

from typing import List
from pydantic import BaseModel, Field
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import json
from datetime import datetime

from flight_agent.config import (
    DEPARTURE_ID, ARRIVAL_ID,
    PROJECT_ID, LOCATION, VERTEX_MODEL
)

# ============================================================
# 구조화된 출력(Structured Output)을 위한 Pydantic Schema
# ============================================================

class SearchParameters(BaseModel):
    origin: str = Field(description="출발지 IATA 코드 (예: ICN)")
    destination: str = Field(description="도착지 IATA 코드 (예: DAD)")
    departure_date: str = Field(description="출발일자 (YYYY-MM-DD 형식)")
    target_price: float = Field(description="목표 가격 (KRW)")

class FlightResult(BaseModel):
    airline: str = Field(description="항공사 이름")
    price: float = Field(description="항공권 가격 (KRW)")
    is_direct: bool = Field(description="직항 여부")
    is_target_met: bool = Field(description="타겟 가격 이하인지 여부")

class FlightSearchResponse(BaseModel):
    search_parameters: SearchParameters = Field(description="검색 조건")
    flight_results: List[FlightResult] = Field(description="항공권 검색 결과 목록")
    summary: str = Field(description="검색 결과에 대한 자연어 요약")

# ============================================================
# 메인 Tool 함수 (ADK Agent가 호출)
# ============================================================

def search_and_analyze_flights() -> dict:
    """
    Vertex AI Gemini 1.5 Flash 모델을 호출하여 인천(ICN)-다낭(DAD) 노선의 항공권을 가상으로 검색하고
    JSON (FlightSearchResponse 규격) 형태로 반환합니다.
    
    Returns:
        규격화된 JSON 데이터를 dict 형태로 파싱하여 반환
    """
    
    print(f"\n{'='*60}")
    print(f"✈  [Gemini 추론] {DEPARTURE_ID} → {ARRIVAL_ID} 항공권 검색 실행")
    print(f"   Vertex AI Model: {VERTEX_MODEL}")
    print(f"{'='*60}")
    
    # Vertex AI 초기화
    import os
    if PROJECT_ID:
        vertexai.init(project=PROJECT_ID, location=os.environ.get("VERTEX_LOCATION", LOCATION))
    
    # 모델 로드
    model = GenerativeModel(VERTEX_MODEL)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 사용자 프롬프트 작성
    prompt = f"""
    당신은 최상급 AI 항공권 에이전트입니다. 오늘 날짜는 {today_str}입니다.
    사용자가 한국 {DEPARTURE_ID}에서 베트남 {ARRIVAL_ID}로 향하는 저렴한 편도 항공권을 찾고 있습니다.
    
    요구사항:
    1. 출발일은 {today_str} 이후의 합리적인 임의의 날짜로 지정하세요.
    2. 역대 데이터를 기반으로 항공권 가격(KRW) 및 항공사 정보를 생성된 결과 3건을 만드세요.
    3. 타겟 가격은 대략 150,000 KRW 로 가정합니다. 가격에 따라 is_target_met 값을 산출하세요.
    
    반드시 응답은 제공된 구조화된 JSON 스키마에 일치하게 출력해주세요.
    """
    
    # v1.5 pydantic schema mapping
    # GenerationConfig.response_schema accepts dict, not object
    schema_dict = FlightSearchResponse.model_json_schema()
    
    generation_config = GenerationConfig(
        response_mime_type="application/json",
        response_schema=schema_dict,
        temperature=0.1
    )
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Pydantic 모델을 활용한 파싱 검증
        json_data = json.loads(response.text)
        validated_response = FlightSearchResponse(**json_data)
        
        print("\n  🏆 모델 예측 결과 수신 및 검증 완료:")
        print(f"     목적지: {validated_response.search_parameters.destination}")
        print(f"     출발일선정: {validated_response.search_parameters.departure_date}")
        print(f"     응답 요약: {validated_response.summary}")
        
        return validated_response.model_dump()
        
    except Exception as e:
        print(f"\n  ❌ 모델 호출 또는 파싱 오류 발생: {str(e)}")
        # 실패 하더라도 규격에 맞는 fallback 데이터를 반환
        return {
            "search_parameters": {
                "origin": DEPARTURE_ID,
                "destination": ARRIVAL_ID,
                "departure_date": today_str,
                "target_price": 0.0
            },
            "flight_results": [],
            "summary": f"검색 중 오류가 발생했습니다: {str(e)}"
        }
