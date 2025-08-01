from pydantic import BaseModel, Field, validator
from typing import List
from ..entities.base import ServiceType, PersonalityType

class TimeRange(BaseModel):
    start: str = Field(..., description="시작 시간 (HH:MM)")
    end: str = Field(..., description="종료 시간 (HH:MM)")

class ConsumerForMatching(BaseModel):
    service_type: ServiceType = Field(..., description="서비스 유형")
    requested_days: str = Field(..., description="요청 요일들 (콤마로 구분)")
    preferred_time: TimeRange = Field(..., description="선호 시간대")
    address: str = Field(..., description="서비스 주소")
    location: List[float] = Field(..., description="서비스 위치 (위도, 경도)")
    personality_type: PersonalityType = Field(..., description="성격 유형")
    
    @validator('location')
    def validate_coordinates(cls, v):
        if not isinstance(v, list) or len(v) != 2:
            raise ValueError('위치는 [위도, 경도] 형태의 리스트여야 합니다')
        
        latitude, longitude = v
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise ValueError('위도와 경도는 숫자여야 합니다')
        
        if not -90 <= latitude <= 90:
            raise ValueError('위도는 -90에서 90 사이의 값이어야 합니다')
        
        if not -180 <= longitude <= 180:
            raise ValueError('경도는 -180에서 180 사이의 값이어야 합니다')
        
        return v

class CaregiverForMatching(BaseModel):
    caregiver_id: str = Field(..., description="요양보호사 ID")
    service_type: ServiceType = Field(..., description="서비스 유형")
    closed_days: str = Field(..., description="휴무일들 (콤마로 구분)")
    available_times: TimeRange = Field(..., description="근무 가능 시간")
    base_address: str = Field(..., description="활동 지역 주소")
    base_location: List[float] = Field(..., description="활동 지역 위치 (위도, 경도)")
    personality_type: PersonalityType = Field(..., description="성격 유형")
    career_years: int = Field(0, description="경력 년수")
    
    @validator('base_location')
    def validate_coordinates(cls, v):
        if not isinstance(v, list) or len(v) != 2:
            raise ValueError('위치는 [위도, 경도] 형태의 리스트여야 합니다')
        
        latitude, longitude = v
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise ValueError('위도와 경도는 숫자여야 합니다')
        
        if not -90 <= latitude <= 90:
            raise ValueError('위도는 -90에서 90 사이의 값이어야 합니다')
        
        if not -180 <= longitude <= 180:
            raise ValueError('경도는 -180에서 180 사이의 값이어야 합니다')
        
        return v

class MatchedCaregiver(BaseModel):
    caregiver_id: str = Field(..., description="요양보호사 ID")
    match_score: float = Field(..., description="매칭 점수")
    reason: str = Field(..., description="매칭 이유")