import os
import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
import httpx
from dotenv import load_dotenv
import pprint
from datetime import datetime

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

# AI 모델 설정
AI_API_KEY = os.getenv("OPENROUTER_API_KEY")
AI_BASE_URL = "https://openrouter.ai/api/v1"

if not AI_API_KEY:
  logger.warning("AI 모델 API 키가 설정되지 않았습니다.")

@router.post("/convert", response_model=ConvertNonStructuredDataToStructuredDataResponse)
async def convert_non_structured_data_to_structured_data(
  request: ConvertNonStructuredDataToStructuredDataRequest
):
  """
  비정형 데이터를 정형 데이터로 변환하는 API
  
  자체 AI 모델을 사용하여 자연어로 작성된 
  요양보호사 근무조건을 구조화된 데이터로 변환합니다.
  """
  pp = pprint.PrettyPrinter(indent=2, width=120, depth=None)
  
  logger.info("=" * 100)
  logger.info("🤖 AI 데이터 변환 요청 시작")
  logger.info("=" * 100)
  start_time = datetime.now()
  
  try:
    # 1. 입력 데이터 검증
    logger.info("\n📋 === 입력 비정형 데이터 분석 ===")
    input_data_info = {
      "데이터 길이": f"{len(request.non_structured_data)}자",
      "입력 내용": request.non_structured_data
    }
    
    for line in pp.pformat(input_data_info).split('\n'):
      logger.info(f"   {line}")
    logger.info("✅ 입력 데이터 분석 완료\n")

    # AI 모델 키 확인
    if not AI_API_KEY:
      logger.error("❌ AI 모델 서비스를 사용할 수 없습니다.")
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="AI 모델 서비스를 사용할 수 없습니다."
      )
      
    # 2. AI 모델 변환 처리
    logger.info("🧠 === AI 모델 변환 처리 시작 ===")
    structured_data = await call_ai_model(request.non_structured_data)
    
    ai_result_info = {
      "변환 상태": "성공",
      "추출된 필드 수": len(structured_data) if isinstance(structured_data, dict) else 0,
      "변환 결과": structured_data
    }
    
    for line in pp.pformat(ai_result_info).split('\n'):
      logger.info(f"   {line}")
    logger.info("✅ AI 모델 변환 완료\n")
      
    # 3. 데이터 구조화 및 검증
    logger.info("🔍 === 데이터 구조화 및 검증 ===")
    response = parse_ai_response(structured_data)
    
    # 구조화된 결과 로깅
    structured_result = {
      "구조화 상태": "성공",
      "최종 변환 데이터": {
        "근무요일": response.day_of_week,
        "근무시간": f"{response.work_start_time} ~ {response.work_end_time}" if response.work_start_time and response.work_end_time else "미지정",
        "근무지역": response.work_area or "미지정",
        "교통수단": response.transportation or "미지정",
        "지원가능질환": response.supported_conditions,
        "서비스유형": response.service_types,
        "기타조건": {
          "점심시간": f"{response.lunch_break}분" if response.lunch_break else "미지정",
          "선호연령": f"{response.preferred_min_age}~{response.preferred_max_age}세" if response.preferred_min_age and response.preferred_max_age else "미지정",
          "선호성별": response.preferred_gender or "미지정"
        }
      }
    }
    
    for line in pp.pformat(structured_result).split('\n'):
      logger.info(f"   {line}")
    logger.info("✅ 데이터 구조화 완료\n")
    
    # 처리 시간 계산
    processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    # 완료 요약
    completion_summary = {
      "변환 상태": "완료",
      "처리시간": f"{processing_time_ms}ms",
      "변환된 필드": len([field for field in [
        response.day_of_week, response.work_start_time, response.work_end_time,
        response.work_area, response.transportation, response.supported_conditions,
        response.service_types, response.preferred_gender
      ] if field is not None and field != []])
    }
    
    logger.info("=" * 100)
    logger.info("✅ === AI 데이터 변환 완료 요약 ===")
    for line in pp.pformat(completion_summary).split('\n'):
      logger.info(f"   {line}")
    logger.info("=" * 100)
    
    return response
      
  except HTTPException:
    logger.error("❌ HTTP 예외 발생")
    raise
  except Exception as e:
    processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    error_info = {
      "변환 상태": "실패",
      "오류 유형": type(e).__name__,
      "오류 내용": str(e),
      "처리시간": f"{processing_time_ms}ms"
    }
    
    logger.error("=" * 100)
    logger.error("❌ === AI 데이터 변환 오류 발생 ===")
    for line in pp.pformat(error_info).split('\n'):
      logger.error(f"   {line}")
    logger.error("=" * 100)
    
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"AI 데이터 변환 중 오류가 발생했습니다: {str(e)}"
    )

def create_conversion_prompt(non_structured_data: str) -> str:
  """AI 모델을 위한 변환 지시사항 생성"""
    
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

async def call_ai_model(non_structured_data: str) -> Dict[str, Any]:
  """자체 AI 모델을 통한 데이터 변환"""
  
  # AI 모델 변환 지시사항 생성
  conversion_instructions = create_conversion_prompt(non_structured_data)
  
  headers = {
    "Authorization": f"Bearer {AI_API_KEY}",
    "Content-Type": "application/json",
  }
    
  payload = {
    "model": "google/gemini-2.5-flash",
    "messages": [
      {
        "role": "system",
        "content": "당신은 요양보호사 근무조건을 분석하는 전문가입니다. 주어진 텍스트를 정확하게 구조화된 데이터로 변환해주세요."
      },
      {
        "role": "user", 
        "content": conversion_instructions
      }
    ],
    "temperature": 0.1,
    "max_tokens": 1000
  }
    
  async with httpx.AsyncClient(timeout=30.0) as client:
    try:
      response = await client.post(
          f"{AI_BASE_URL}/chat/completions",
          headers=headers,
          json=payload
      )
        
      if response.status_code != 200:
          error_detail = response.text
          logger.error(f"AI 모델 처리 오류: {response.status_code}")
          raise HTTPException(
              status_code=status.HTTP_502_BAD_GATEWAY,
              detail=f"AI 모델 처리 실패: {response.status_code}"
          )
        
      result = response.json()
        
      if "choices" not in result or not result["choices"]:
          logger.error("❌ AI 모델 응답 오류")
          raise HTTPException(
              status_code=status.HTTP_502_BAD_GATEWAY,
              detail="AI 모델 응답 오류"
          )
        
      content = result["choices"][0]["message"]["content"]
        
        # JSON 파싱
      try:
        # 마크다운 코드블록 제거
        content = content.strip()
        if content.startswith('```json'):
          content = content[7:]
        if content.startswith('```'):
          content = content[3:]
        if content.endswith('```'):
          content = content[:-3]
        content = content.strip()
        
        parsed_json = json.loads(content)
        return parsed_json
      except json.JSONDecodeError as e:
        logger.error(f"AI 응답 데이터 파싱 오류")
        raise HTTPException(
          status_code=status.HTTP_502_BAD_GATEWAY,
          detail="AI 응답 데이터 파싱 오류"
        )
            
    except httpx.TimeoutException:
      logger.error("❌ AI 모델 응답 시간 초과")
      raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail="AI 모델 응답 시간 초과"
      )
    except httpx.RequestError as e:
      logger.error(f"AI 모델 연결 오류: {str(e)}")
      raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="AI 모델 연결 오류"
      )

def parse_ai_response(ai_data: Dict[str, Any]) -> ConvertNonStructuredDataToStructuredDataResponse:
    """AI 응답을 DTO로 변환"""
    pp = pprint.PrettyPrinter(indent=2, width=120, depth=None)
    
    try:
      # 요일 데이터 변환
      day_of_week = []
      if "day_of_week" in ai_data and ai_data["day_of_week"]:
        valid_days = [day.value for day in DayOfWeek]
        day_of_week = [day for day in ai_data["day_of_week"] if day in valid_days]
      
      # 지원 질환 데이터 변환
      supported_conditions = []
      if "supported_conditions" in ai_data and ai_data["supported_conditions"]:
        valid_conditions = [condition.value for condition in Disease]
        supported_conditions = [condition for condition in ai_data["supported_conditions"] if condition in valid_conditions]
      
      # 선호 성별 데이터 변환
      preferred_gender = None
      if "preferred_gender" in ai_data and ai_data["preferred_gender"]:
        valid_genders = [gender.value for gender in PreferredGender]
        if ai_data["preferred_gender"] in valid_genders:
          preferred_gender = ai_data["preferred_gender"]
      
      # 서비스 유형 데이터 변환
      service_types = []
      if "service_types" in ai_data and ai_data["service_types"]:
        valid_service_types = [service_type.value for service_type in ServiceType]
        service_types = [service_type for service_type in ai_data["service_types"] if service_type in valid_service_types]
      
      # 응답 DTO 생성
      response = ConvertNonStructuredDataToStructuredDataResponse(
        day_of_week=day_of_week,
        work_start_time=ai_data.get("work_start_time"),
        work_end_time=ai_data.get("work_end_time"),
        work_min_time=ai_data.get("work_min_time"),
        work_max_time=ai_data.get("work_max_time"),
        available_time=ai_data.get("available_time"),
        work_area=ai_data.get("work_area"),
        transportation=ai_data.get("transportation"),
        lunch_break=ai_data.get("lunch_break"),
        buffer_time=ai_data.get("buffer_time"),
        supported_conditions=supported_conditions,
        preferred_min_age=ai_data.get("preferred_min_age"),
        preferred_max_age=ai_data.get("preferred_max_age"),
        preferred_gender=preferred_gender,
        service_types=service_types
      )
      
      return response
        
    except Exception as e:
      logger.error(f"데이터 구조화 중 오류: {str(e)}")
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="데이터 구조화 중 오류가 발생했습니다."
      )
