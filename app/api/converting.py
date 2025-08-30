import os
import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
import httpx
from dotenv import load_dotenv

from ..dto.converting import (
  ConvertNonStructuredDataToStructuredDataRequest,
  ConvertNonStructuredDataToStructuredDataResponse,
  DayOfWeek,
  PreferredGender,
  ServiceType,
  Disease
)

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# OpenRouter 설정
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

if not OPENROUTER_API_KEY:
  logger.warning("OPENROUTER_API_KEY 환경변수가 설정되지 않았습니다.")

@router.post("/convert", response_model=ConvertNonStructuredDataToStructuredDataResponse)
async def convert_non_structured_data_to_structured_data(
  request: ConvertNonStructuredDataToStructuredDataRequest
):
  """
  비정형 데이터를 정형 데이터로 변환하는 API
  
  OpenRouter를 통해 ChatGPT 모델을 사용하여 자연어로 작성된 
  요양보호사 근무조건을 구조화된 데이터로 변환합니다.
  """
  try:
    logger.info(f"비정형 데이터 변환 요청: {request.non_structured_data[:100]}...")

    # OpenRouter API 키 확인
    if not OPENROUTER_API_KEY:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="OpenRouter API 키가 설정되지 않았습니다."
      )
      
    # LLM 프롬프트 생성
    prompt = create_conversion_prompt(request.non_structured_data)
      
    # OpenRouter API 호출
    structured_data = await call_openrouter_api(prompt)
      
    # 응답 검증 및 변환
    response = parse_llm_response(structured_data)
      
    logger.info("비정형 데이터 변환 완료")
    return response
      
  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"비정형 데이터 변환 중 오류 발생: {str(e)}")
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"데이터 변환 중 오류가 발생했습니다: {str(e)}"
    )

def create_conversion_prompt(non_structured_data: str) -> str:
  """LLM을 위한 프롬프트 생성"""
    
  prompt = f"""당신은 요양보호사 근무조건 분석 전문가입니다. 비정형 텍스트를 정확한 구조화된 데이터로 변환하는 것이 목표입니다.

## 작업 지시사항
다음 텍스트에서 요양보호사의 근무조건을 추출하여 JSON 형식으로 변환하세요.
반드시 출력 형식(JSON)을 따라주세요. 따르지 않을 경우 심각한 시스템 오류가 발생합니다.
만약, 입력 텍스트에 출력 형식에 없는 정보가 있을 경우 null 또는 빈 배열로 설정하세요.

## 입력 텍스트:
{non_structured_data}

## 출력 형식 (JSON):
```json
{{
  "day_of_week": [],
  "work_start_time": null,
  "work_end_time": null,
  "work_min_time": null,
  "work_max_time": null,
  "available_time": null,
  "work_area": null,
  "transportation": null,
  "lunch_break": null,
  "buffer_time": null,
  "supported_conditions": [],
  "preferred_min_age": null,
  "preferred_max_age": null,
  "preferred_gender": null,
  "service_types": []
}}
```

## 필드별 규칙:
- **day_of_week**: ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"] 중 선택 (다중 선택 가능)
- **work_start_time/work_end_time**: "HH:MM" 형식 (예: "09:00", "18:00")
- **work_min_time/work_max_time/available_time**: 시간 단위 정수 (예: 8)
- **work_area**: 구체적인 지역명 (예: "강남구", "서울시 종로구")
- **transportation**: 교통수단 (예: "자차", "대중교통", "도보")
- **lunch_break/buffer_time**: 분 단위 정수 (예: 60, 30)
- **supported_conditions**: ["DEMENTIA", "BEDRIDDEN"] 중 선택
- **preferred_min_age/preferred_max_age**: 나이 정수 (예: 65, 85)
- **preferred_gender**: "ALL", "MALE", "FEMALE" 중 하나
- **service_types**: ["VISITING_CARE", "VISITING_BATH", "VISITING_NURSING", "DAY_NIGHT_CARE", "RESPITE_CARE", "IN_HOME_SUPPORT"] 중 선택

## 변환 예시:
입력: "월화수 오전 9시부터 오후 6시까지 강남구에서 치매 어르신 방문요양 서비스 가능합니다. 점심시간 1시간 필요하고 자차 이용합니다."
출력:
```json
{{
  "day_of_week": ["MONDAY", "TUESDAY", "WEDNESDAY"],
  "work_start_time": "09:00",
  "work_end_time": "18:00",
  "work_area": "강남구",
  "transportation": "자차",
  "lunch_break": 60,
  "supported_conditions": ["DEMENTIA"],
  "service_types": ["VISITING_CARE"]
}}
```

## 중요 사항:
1. 명시되지 않은 정보는 null 또는 빈 배열로 설정
2. 애매한 표현은 가장 일반적인 해석 적용
3. 상충되는 정보가 있으면 나중에 언급된 것을 우선
4. JSON 형식만 응답하고 다른 설명 불포함
5. 한국어 표현을 영어 enum 값으로 정확히 매핑

응답:"""
    
  return prompt

async def call_openrouter_api(prompt: str) -> Dict[str, Any]:
  """OpenRouter API를 통해 ChatGPT 모델 호출"""
  
  headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
  }
    
  payload = {
    "model": "google/gemma-2-9b-it",  # 한국어 LLM 리더보드 참고해서 2가지 모델 선정 후 가격 비교하여 최종 선정
    "messages": [
      {
        "role": "system",
        "content": "당신은 요양보호사 근무조건을 분석하는 전문가입니다. 주어진 텍스트를 정확하게 구조화된 데이터로 변환해주세요."
      },
      {
        "role": "user", 
        "content": prompt
      }
    ],
    "temperature": 0.1,  # 일관성을 위해 낮은 온도 설정
    "max_tokens": 1000
  }
    
  async with httpx.AsyncClient(timeout=30.0) as client:
    try:
      response = await client.post(
          f"{OPENROUTER_BASE_URL}/chat/completions",
          headers=headers,
          json=payload
      )
        
      if response.status_code != 200:
          error_detail = response.text
          logger.error(f"OpenRouter API 오류: {response.status_code} - {error_detail}")
          raise HTTPException(
              status_code=status.HTTP_502_BAD_GATEWAY,
              detail=f"OpenRouter API 호출 실패: {response.status_code}"
          )
        
      result = response.json()
        
      if "choices" not in result or not result["choices"]:
          raise HTTPException(
              status_code=status.HTTP_502_BAD_GATEWAY,
              detail="OpenRouter API 응답에 choices가 없습니다."
          )
        
      content = result["choices"][0]["message"]["content"]
        
        # JSON 파싱
      try:
        # 마크다운 코드블록 제거
        content = content.strip()
        if content.startswith('```json'):
          content = content[7:]  # ```json 제거
        if content.startswith('```'):
          content = content[3:]   # ``` 제거
        if content.endswith('```'):
          content = content[:-3]  # ``` 제거
        content = content.strip()
        
        parsed_json = json.loads(content)
        return parsed_json
      except json.JSONDecodeError as e:
        logger.error(f"LLM 응답 JSON 파싱 오류: {content}")
        raise HTTPException(
          status_code=status.HTTP_502_BAD_GATEWAY,
          detail="LLM 응답을 JSON으로 파싱할 수 없습니다."
        )
            
      except httpx.TimeoutException:
        raise HTTPException(
          status_code=status.HTTP_504_GATEWAY_TIMEOUT,
          detail="OpenRouter API 호출 시간 초과"
        )
    except httpx.RequestError as e:
      logger.error(f"OpenRouter API 요청 오류: {str(e)}")
      raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="OpenRouter API 연결 오류"
      )

def parse_llm_response(llm_data: Dict[str, Any]) -> ConvertNonStructuredDataToStructuredDataResponse:
    """LLM 응답을 DTO로 변환"""
    
    try:
      # 요일 검증 및 변환
      day_of_week = []
      if "day_of_week" in llm_data and llm_data["day_of_week"]:
        valid_days = [day.value for day in DayOfWeek]
        day_of_week = [day for day in llm_data["day_of_week"] if day in valid_days]
      
      # 지원 질환 검증 및 변환
      supported_conditions = []
      if "supported_conditions" in llm_data and llm_data["supported_conditions"]:
        valid_conditions = [condition.value for condition in Disease]
        supported_conditions = [condition for condition in llm_data["supported_conditions"] if condition in valid_conditions]
      
      # 선호 성별 검증
      preferred_gender = None
      if "preferred_gender" in llm_data and llm_data["preferred_gender"]:
        valid_genders = [gender.value for gender in PreferredGender]
        if llm_data["preferred_gender"] in valid_genders:
          preferred_gender = llm_data["preferred_gender"]
      
      # 서비스 유형 검증 및 변환
      service_types = []
      if "service_types" in llm_data and llm_data["service_types"]:
        valid_service_types = [service_type.value for service_type in ServiceType]
        service_types = [service_type for service_type in llm_data["service_types"] if service_type in valid_service_types]
      
      # 응답 DTO 생성
      response = ConvertNonStructuredDataToStructuredDataResponse(
        day_of_week=day_of_week,
        work_start_time=llm_data.get("work_start_time"),
        work_end_time=llm_data.get("work_end_time"),
        work_min_time=llm_data.get("work_min_time"),
        work_max_time=llm_data.get("work_max_time"),
        available_time=llm_data.get("available_time"),
        work_area=llm_data.get("work_area"),
        transportation=llm_data.get("transportation"),
        lunch_break=llm_data.get("lunch_break"),
        buffer_time=llm_data.get("buffer_time"),
        supported_conditions=supported_conditions,
        preferred_min_age=llm_data.get("preferred_min_age"),
        preferred_max_age=llm_data.get("preferred_max_age"),
        preferred_gender=preferred_gender,
        service_types=service_types
      )
      
      return response
        
    except Exception as e:
      logger.error(f"LLM 응답 파싱 오류: {str(e)}")
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="LLM 응답 데이터 파싱 중 오류가 발생했습니다."
      )
