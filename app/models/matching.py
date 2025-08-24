from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class Location(BaseModel):
    """위치 정보 모델"""
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('위도는 -90에서 90 사이의 값이어야 합니다')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('경도는 -180에서 180 사이의 값이어야 합니다')
        return v

class ServiceRequest(BaseModel):
    """서비스 요청 모델 - DB 스키마 기반"""
    service_request_id: str = Field(..., description="서비스 요청 ID (UUID)")
    consumer_id: str = Field(..., description="이용자 ID")
    service_address: str = Field(..., description="서비스 주소")
    address_type: Optional[str] = Field(None, description="주소 유형")
    location: str = Field(..., description="위치 정보 (위도,경도 문자열)")
    preferred_time: Optional[str] = Field(None, description="선호 시간")
    duration: Optional[str] = Field(None, description="서비스 기간")
    service_type: Optional[str] = Field(None, description="서비스 유형")
    request_status: Optional[str] = Field(None, description="요청 상태")
    request_date: Optional[str] = Field(None, description="요청 날짜")
    additional_information: Optional[str] = Field(None, description="추가 정보")
    
    def get_location_coordinates(self) -> List[float]:
        """위치 문자열을 [위도, 경도] 리스트로 변환"""
        try:
            lat, lng = map(float, self.location.split(','))
            return [lat, lng]
        except (ValueError, AttributeError):
            raise ValueError("위치 정보 형식이 올바르지 않습니다")

class Caregiver(BaseModel):
    """요양보호사 모델 - DB 스키마 기반"""
    caregiver_id: str = Field(..., description="요양보호사 ID (UUID)")
    user_id: str = Field(..., description="사용자 ID (UUID)")
    available_times: Optional[str] = Field(None, description="가능 시간")
    address: Optional[str] = Field(None, description="주소")
    service_type: Optional[str] = Field(None, description="서비스 유형")
    days_off: Optional[str] = Field(None, description="휴무일")
    career: Optional[str] = Field(None, description="경력")
    korean_proficiency: Optional[str] = Field(None, description="한국어 실력")
    is_accompany_outing: Optional[bool] = Field(None, description="외출 동행 가능 여부")
    self_introduction: Optional[str] = Field(None, description="자기소개")
    is_verified: Optional[bool] = Field(None, description="검증 여부")

class CaregiverPreference(BaseModel):
    """요양보호사 선호도 모델 - DB 스키마 기반"""
    caregiver_preference_id: str = Field(..., description="요양보호사 선호도 ID")
    caregiver_id: str = Field(..., description="요양보호사 ID (UUID)")
    work_days: Optional[str] = Field(None, description="근무일")
    work_start_end_time: Optional[str] = Field(None, description="근무 시작/종료 시간")
    min_max_work_time: Optional[str] = Field(None, description="최소/최대 근무 시간")
    available_time: Optional[str] = Field(None, description="가능 시간")
    work_area: Optional[str] = Field(None, description="근무 지역")
    transportation: Optional[str] = Field(None, description="교통수단")
    lunch_break: Optional[str] = Field(None, description="점심 휴게시간")
    buffer_time: Optional[str] = Field(None, description="버퍼 시간")
    supported_conditions: Optional[str] = Field(None, description="지원 가능 조건")
    preferred_age_group: Optional[str] = Field(None, description="선호 연령대")
    preferred_gender: Optional[str] = Field(None, description="선호 성별")

class CaregiverForMatching(BaseModel):
    """매칭용 요양보호사 모델 - 매칭 알고리즘에 필요한 정보만 포함"""
    caregiver_id: str = Field(..., description="요양보호사 ID")
    base_location: List[float] = Field(..., description="활동 지역 위치 (위도, 경도)")
    career_years: int = Field(0, description="경력 년수")
    available_times: Optional[str] = Field(None, description="가능 시간")
    service_type: Optional[str] = Field(None, description="서비스 유형")
    days_off: Optional[str] = Field(None, description="휴무일")
    work_area: Optional[str] = Field(None, description="근무 지역")
    
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

class ServiceMatch(BaseModel):
    """서비스 매칭 모델 - DB 스키마 기반"""
    service_match_id: str = Field(..., description="서비스 매칭 ID (UUID)")
    service_request_id: str = Field(..., description="서비스 요청 ID (UUID)")
    caregiver_id: str = Field(..., description="요양보호사 ID (UUID)")
    match_status: Optional[str] = Field(None, description="매칭 상태")
    service_time: Optional[str] = Field(None, description="서비스 시간")
    service_date: Optional[str] = Field(None, description="서비스 날짜")

class MatchedCaregiver(BaseModel):
    """매칭된 요양보호사 정보 - 매칭 결과용"""
    caregiver_id: str = Field(..., description="요양보호사 ID")
    match_score: float = Field(..., description="매칭 점수")
    reason: str = Field(..., description="매칭 이유")
    distance_km: Optional[float] = Field(None, description="거리 (km)")
    estimated_travel_time: Optional[int] = Field(None, description="예상 이동 시간 (분)")