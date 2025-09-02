from typing import List, Optional, Set
from pydantic import BaseModel
from enum import Enum


class ConvertNonStructuredDataToStructuredDataRequest(BaseModel):
    """비정형 데이터를 정형 데이터로 변환하는 요청 DTO"""
    non_structured_data: str


class ConvertNonStructuredDataToStructuredDataResponse(BaseModel):
    """비정형 데이터를 정형 데이터로 변환한 응답 DTO"""
    
    # 근무 가능 요일 (Set<DayOfWeek> -> List[str])
    day_of_week: List[str] = []
    
    # 근무 시간 (LocalTime -> str in HH:MM format)
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    
    # 근무 시간 범위 (Integer -> Optional[int])
    work_min_time: Optional[int] = None
    work_max_time: Optional[int] = None
    available_time: Optional[int] = None
    
    # 근무 지역 및 교통수단 (String -> Optional[str])
    work_area: Optional[str] = None
    transportation: Optional[str] = None
    
    # 휴게 및 버퍼 시간 (Integer -> Optional[int])
    lunch_break: Optional[int] = None
    buffer_time: Optional[int] = None
    
    # 지원 가능 질환 (Set<Disease> -> List[str])
    supported_conditions: List[str] = []
    
    # 선호 연령 범위 (Integer -> Optional[int])
    preferred_min_age: Optional[int] = None
    preferred_max_age: Optional[int] = None
    
    # 선호 성별 (PreferredGender -> Optional[str])
    preferred_gender: Optional[str] = None
    
    # 서비스 유형 (Set<ServiceType> -> List[str])
    service_types: List[str] = []


# 참고용 Enum 클래스들 (실제 사용 시 프로젝트 요구사항에 맞게 조정)
class DayOfWeek(str, Enum):
    """요일 열거형"""
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class PreferredGender(str, Enum):
    """선호 성별 열거형"""
    ALL = "ALL"
    MALE = "MALE"
    FEMALE = "FEMALE"


class ServiceType(str, Enum):
    """서비스 유형 열거형"""
    VISITING_CARE = "VISITING_CARE"      # 방문 요양
    VISITING_BATH = "VISITING_BATH"      # 방문 목욕
    VISITING_NURSING = "VISITING_NURSING"   # 방문 간호
    DAY_NIGHT_CARE = "DAY_NIGHT_CARE"     # 주야간 보호
    RESPITE_CARE = "RESPITE_CARE"       # 단기 보호
    IN_HOME_SUPPORT = "IN_HOME_SUPPORT"     # 재가 요양 지원


class Disease(str, Enum):
    """지원 가능 질환 열거형"""
    DEMENTIA = "DEMENTIA"  # 치매
    BEDRIDDEN = "BEDRIDDEN"  # 와상
