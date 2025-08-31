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

# 매칭 API에서 사용하는 DTO 클래스들 추가
class ServiceRequestDTO(BaseModel):
    """서비스 요청 DTO"""
    serviceRequestId: str = Field(..., description="서비스 요청 ID")
    consumerId: str = Field(..., description="소비자 ID")
    serviceAddress: str = Field(..., description="서비스 주소")
    addressType: Optional[str] = Field(None, description="주소 유형")
    location: str = Field(..., description="위치 (위도,경도)")
    requestDate: Optional[str] = Field(None, description="요청 날짜")
    preferredStartTime: Optional[str] = Field(None, description="선호 시작 시간")
    preferredEndTime: Optional[str] = Field(None, description="선호 종료 시간")
    duration: Optional[str] = Field(None, description="서비스 시간")
    serviceType: Optional[str] = Field(None, description="서비스 유형")
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
    preferences: Optional[CaregiverPreference] = Field(None, description="선호 조건")

class MatchedCaregiverDTO(BaseModel):
    """매칭된 요양보호사 DTO"""
    caregiverId: str = Field(..., description="요양보호사 ID")
    name: Optional[str] = Field(None, description="이름")
    distance: float = Field(..., description="거리 (km)")
    estimatedTravelTime: Optional[int] = Field(None, description="예상 이동 시간 (분)")
    matchingScore: Optional[float] = Field(None, description="매칭 점수")
    address: Optional[str] = Field(None, description="주소")
    addressType: Optional[str] = Field(None, description="주소 유형")
    location: Optional[str] = Field(None, description="위치 (위도,경도)")
    career: Optional[str] = Field(None, description="경력")
    selfIntroduction: Optional[str] = Field(None, description="자기소개")

class MatchingRequestDTO(BaseModel):
    """매칭 요청 DTO"""
    serviceRequest: ServiceRequestDTO = Field(..., description="서비스 요청 정보")
    candidateCaregivers: List[CaregiverForMatchingDTO] = Field(..., description="후보 요양보호사 목록")

class MatchingResponseDTO(BaseModel):
    """매칭 응답 DTO"""
    serviceRequestId: str = Field(..., description="서비스 요청 ID")
    matchedCaregivers: List[MatchedCaregiverDTO] = Field(..., description="매칭된 요양보호사 목록")
    totalCandidates: int = Field(..., description="전체 후보자 수")
    matchedCount: int = Field(..., description="매칭된 요양보호사 수")
    processingTimeMs: Optional[int] = Field(None, description="처리 시간 (밀리초)")