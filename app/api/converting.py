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
    
    prompt = f"""
다음 비정형 텍스트를 분석하여 요양보호사의 근무조건을 구조화된 JSON 형태로 변환해주세요.

입력 텍스트:
{non_structured_data}

다음 JSON 스키마에 맞춰 응답해주세요. 정보가 없는 필드는 null 또는 빈 배열로 설정하세요:

{{
  "day_of_week": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"],
  "work_start_time": "HH:MM",
  "work_end_time": "HH:MM", 
  "work_min_time": 숫자(시간),
  "work_max_time": 숫자(시간),
  "available_time": 숫자(시간),
  "work_area": "지역명",
  "transportation": "교통수단",
  "lunch_break": 숫자(분),
  "buffer_time": 숫자(분),
  "supported_conditions": ["DEMENTIA", "BEDRIDDEN"],
  "preferred_min_age": 숫자,
  "preferred_max_age": 숫자,
  "preferred_gender": "ALL" | "MALE" | "FEMALE",
  "service_types": ["VISITING_CARE", "VISITING_BATH", "VISITING_NURSING", "DAY_NIGHT_CARE", "RESPITE_CARE", "IN_HOME_SUPPORT"]
}}

변환 규칙:
1. 요일: MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY 중 선택
2. 시간: HH:MM 형식 (24시간제)
3. 지원 질환: DEMENTIA(치매), BEDRIDDEN(와상) 중 선택
4. 선호 성별: ALL(무관), MALE(남성), FEMALE(여성) 중 선택  
5. 서비스 유형: VISITING_CARE(방문요양), VISITING_BATH(방문목욕), VISITING_NURSING(방문간호), DAY_NIGHT_CARE(주야간보호), RESPITE_CARE(단기보호), IN_HOME_SUPPORT(재가요양지원) 중 선택

JSON만 응답하고 다른 설명은 포함하지 마세요.
"""
    
    return prompt

async def call_openrouter_api(prompt: str) -> Dict[str, Any]:
    """OpenRouter API를 통해 ChatGPT 모델 호출"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "google/gemma-2-9b-it",  # 비용 효율적인 모델 사용
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
                return json.loads(content)
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
