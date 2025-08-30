from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import time, date

class LocationInfo(BaseModel):
    """위치 정보 DTO - 새로운 형식"""
    roadAddress: str = Field(..., description="도로명 주소")
    jibunAddress: str = Field(..., description="지번 주소")
    addressElements: List[Dict[str, Any]] = Field(..., description="주소 구성 요소")
    x: float = Field(..., description="경도 (float)")
    y: float = Field(..., description="위도 (float)")
    
    def get_coordinates(self) -> List[float]:
        """위도, 경도를 [위도, 경도] 리스트로 반환 (기존 코드 호환성)"""
        return [self.y, self.x]

class ServiceRequest(BaseModel):
    service_request_id: str
    consumer_id: str
    service_address: str
    address_type: Optional[str]
    location: str  # "위도,경도" 문자열
    request_date: Optional[str]
    preferred_start_time: Optional[str]
    preferred_end_time: Optional[str]
    duration: Optional[str]
    service_type: Optional[str]
    request_status: Optional[str]
    additional_information: Optional[str]

class Caregiver(BaseModel):
    caregiver_id: str
    user_id: str
    address: Optional[str]
    career: Optional[str]
    korean_proficiency: Optional[str]
    is_accompany_outing: Optional[bool]
    self_introduction: Optional[str]
    verified_status: Optional[str]


class CaregiverPreference(BaseModel):
    caregiver_preference_id: str
    caregiver_id : str
    day_of_week : List[str]
    work_start_time : Optional[str]
    work_end_time : Optional[str]
    work_min_time : Optional[str]
    work_max_time : Optional[str]
    available_time : Optional[str]
    work_area : Optional[str]
    transportation : Optional[str]
    lunch_break : Optional[str]
    buffer_time : Optional[str]
    supported_conditions : List[str]
    preferred_min_age : Optional[str]
    preferred_max_age : Optional[str]
    preferred_gender : Optional[str]
    service_types: List[str]