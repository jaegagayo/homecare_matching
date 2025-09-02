from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import time, date

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
    address_type : Optional[str]
    location : Optional[str]  # "위도,경도" 문자열
    transportation : Optional[str]
    lunch_break : Optional[str]
    buffer_time : Optional[str]
    supported_conditions : List[str]
    preferred_min_age : Optional[str]
    preferred_max_age : Optional[str]
    preferred_gender : Optional[str]
    service_types: List[str]

# 위치 정보를 위한 별도 클래스
class LocationDTO(BaseModel):
    """위치 정보 DTO"""
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")

# 매칭 API에서 사용하는 DTO 클래스들 추가
class ServiceRequestDTO(BaseModel):
    """서비스 요청 DTO"""
    serviceRequestId: Optional[str] = Field(None, description="서비스 요청 ID (서버에서 생성)")
    consumerId: str = Field(..., description="소비자 ID")
    serviceAddress: str = Field(..., description="서비스 주소")
    addressType: Optional[str] = Field(None, description="주소 유형 (ROAD, JIBUN, APARTMENT, etc.)")
    location: LocationDTO = Field(..., description="위치 정보")
    requestDate: Optional[str] = Field(None, description="요청 날짜 (YYYY-MM-DD)")
    preferredStartTime: Optional[str] = Field(None, description="선호 시작 시간 (HH:MM:SS)")
    preferredEndTime: Optional[str] = Field(None, description="선호 종료 시간 (HH:MM:SS)")
    duration: Optional[int] = Field(None, description="서비스 시간 (분 단위)")
    serviceType: Optional[str] = Field(None, description="서비스 유형 (VISITING_CARE, etc.)")
    additionalInformation: Optional[str] = Field(None, description="추가 정보")

class CaregiverForMatchingDTO(BaseModel):
    """매칭용 요양보호사 DTO"""
    caregiverId: str = Field(..., description="요양보호사 ID")
    userId: str = Field(..., description="사용자 ID")
    name: Optional[str] = Field(None, description="이름")
    address: Optional[str] = Field(None, description="주소")
    addressType: Optional[str] = Field(None, description="주소 유형")
    location: Optional[str] = Field(None, description="위치 (위도,경도)")
    career: Optional[str] = Field(None, description="경력")
    koreanProficiency: Optional[str] = Field(None, description="한국어 능력")
    isAccompanyOuting: Optional[bool] = Field(None, description="외출 동행 가능 여부")
    selfIntroduction: Optional[str] = Field(None, description="자기소개")
    verifiedStatus: Optional[str] = Field(None, description="인증 상태")
    # 매칭 처리를 위한 추가 속성들
    workStartTime: Optional[str] = Field(None, description="근무 시작 시간")
    workEndTime: Optional[str] = Field(None, description="근무 종료 시간")
    workArea: Optional[str] = Field(None, description="근무 지역")
    baseLocation: Optional[str] = Field(None, description="기본 위치 (위도,경도)")
    careerYears: Optional[int] = Field(None, description="경력 연수")
    transportation: Optional[str] = Field(None, description="교통수단")
    serviceType: Optional[str] = Field(None, description="서비스 유형")
    preferences: Optional[CaregiverPreference] = Field(None, description="선호 조건")

class MatchedCaregiverDTO(BaseModel):
    """매칭된 요양보호사 DTO"""
    caregiverId: str = Field(..., description="요양보호사 ID")
    name: Optional[str] = Field(None, description="이름")
    distanceKm: float = Field(..., description="거리 (km)")
    estimatedTravelTime: Optional[int] = Field(None, description="예상 이동 시간 (분)")
    matchScore: Optional[int] = Field(None, description="매칭 순위 (1, 2, 3, 4, 5)")
    matchReason: Optional[str] = Field(None, description="매칭 이유")
    address: Optional[str] = Field(None, description="주소")
    addressType: Optional[str] = Field(None, description="주소 유형")
    location: Optional[str] = Field(None, description="위치 (위도,경도)")
    career: Optional[str] = Field(None, description="경력")
    selfIntroduction: Optional[str] = Field(None, description="자기소개")
    isVerified: Optional[bool] = Field(None, description="인증 여부")
    serviceType: Optional[str] = Field(None, description="서비스 유형")

class MatchingRequestDTO(BaseModel):
    """매칭 요청 DTO"""
    serviceRequest: ServiceRequestDTO = Field(..., description="서비스 요청 정보")

class MatchingResponseDTO(BaseModel):
    """매칭 응답 DTO"""
    serviceRequestId: str = Field(..., description="서비스 요청 ID")
    matchedCaregivers: List[MatchedCaregiverDTO] = Field(..., description="매칭된 요양보호사 목록")
    totalCandidates: int = Field(..., description="전체 후보자 수")
    matchedCount: int = Field(..., description="매칭된 요양보호사 수")
    processingTimeMs: Optional[int] = Field(None, description="처리 시간 (밀리초)")