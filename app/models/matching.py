from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class LocationInfo(BaseModel):
    """위치 정보 모델 - 새로운 형식"""
    roadAddress: str = Field(..., description="도로명 주소")
    jibunAddress: str = Field(..., description="지번 주소")
    addressElements: List[Dict[str, Any]] = Field(..., description="주소 구성 요소")
    x: float = Field(..., description="경도 (float)")
    y: float = Field(..., description="위도 (float)")
    
    def get_coordinates(self) -> List[float]:
        """위도, 경도를 [위도, 경도] 리스트로 반환 (기존 코드 호환성)"""
        return [self.y, self.x]

class ServiceRequest(BaseModel):
    """서비스 요청 모델 - DB 스키마 기반"""
    service_request_id: str = Field(..., description="서비스 요청 ID (UUID)")
    consumer_id: str = Field(..., description="이용자 ID")
    service_address: str = Field(..., description="서비스 주소")
    address_type: Optional[str] = Field(None, description="주소 유형")
    location: LocationInfo = Field(..., description="위치 정보")
    preferred_start_time: Optional[str] = Field(None, description="선호 시간 (시작)")
    preferred_end_time: Optional[str] = Field(None, description="선호 시간 (끝)")
    duration: Optional[int] = Field(None, description="1회 소요 시간")
    service_type: Optional[str] = Field(None, description="서비스 유형")
    requestStatus: Optional[str] = Field(None, description="요청 상태")
    requestDate: Optional[str] = Field(None, description="요청 날짜")
    additional_information: Optional[str] = Field(None, description="추가 정보")

class Caregiver(BaseModel):
    """요양보호사 모델 - DB 스키마 기반"""
    caregiver_id: str = Field(..., description="요양보호사 ID (UUID)")
    user_id: str = Field(..., description="사용자 ID (UUID)")
    available_times: Optional[str] = Field(None, description="가능 시간")
    address: Optional[str] = Field(None, description="주소")
    service_type: Optional[str] = Field(None, description="서비스 유형")
    days_off: Optional[str] = Field(None, description="휴무일")
    career: Optional[int] = Field(None, description="경력")
    koreanProficiency: Optional[str] = Field(None, description="한국어 실력")
    is_accompany_outing: Optional[bool] = Field(None, description="외출 동행 가능 여부")
    self_introduction: Optional[str] = Field(None, description="자기소개")
    verifiedStatus: Optional[str] = Field(None, description="검증 상태")

class CaregiverPreference(BaseModel):
    """요양보호사 선호도 모델 - DB 스키마 기반"""
    caregiver_preference_id: str = Field(..., description="요양보호사 선호도 ID")
    caregiver_id: str = Field(..., description="요양보호사 ID (UUID)")
    day_of_week: Optional[List[str]] = Field(None, description="근무 가능 요일")
    work_start_time: Optional[str] = Field(None, description="근무 시작 시간")
    work_end_time: Optional[str] = Field(None, description="근무 종료 시간")
    work_min_time: Optional[int] = Field(None, description="최소 근무 시간 (Integer)")
    work_max_time: Optional[int] = Field(None, description="최대 근무 시간 (Integer)")
    available_time: Optional[str] = Field(None, description="가능 시간")
    work_area: Optional[str] = Field(None, description="근무 지역")
    transportation: Optional[str] = Field(None, description="교통수단")
    lunch_break: Optional[str] = Field(None, description="점심 휴게시간")
    buffer_time: Optional[str] = Field(None, description="버퍼 시간")
    supportedConditions: Optional[List[str]] = Field(None, description="지원 가능 질환")
    preferred_min_age: Optional[int] = Field(None, description="선호 최소 연령 (Integer)")
    preferred_max_age: Optional[int] = Field(None, description="선호 최대 연령 (Integer)")
    preferred_gender: Optional[str] = Field(None, description="선호 성별")
    service_types: Optional[List[str]] = Field(None, description="서비스 유형")

class CaregiverForMatching(BaseModel):
    """매칭용 요양보호사 모델 - 매칭 알고리즘에 필요한 정보만 포함"""
    caregiver_id: str = Field(..., description="요양보호사 ID")
    base_location: LocationInfo = Field(..., description="활동 지역 위치 정보")
    career_years: int = Field(0, description="경력 년수")
    work_area: Optional[str] = Field(None, description="근무 지역")

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