from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date

class ServiceRequestDTO(BaseModel):
    """서비스 요청 정보 DTO - DB 스키마 기반"""
    serviceRequestId: str = Field(..., description="서비스 요청 ID")
    consumerId: str = Field(..., description="이용자 ID")
    serviceAddress: str = Field(..., description="서비스 주소")
    addressType: Optional[str] = Field(None, description="주소 유형")
    location: List[float] = Field(..., description="서비스 요청 위치 (위도, 경도)")
    preferredTime: Optional[str] = Field(None, description="선호 시간")
    duration: Optional[str] = Field(None, description="서비스 기간")
    serviceType: Optional[str] = Field(None, description="서비스 유형")
    requestStatus: Optional[str] = Field('PENDING', description="요청 상태")
    requestDate: Optional[str] = Field(None, description="요청 날짜")
    additionalInformation: Optional[str] = Field(None, description="추가 정보")
    
    @validator('location')
    def validate_service_coordinates(cls, v):
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
    

class CaregiverForMatchingDTO(BaseModel):
    """매칭용 요양보호사 정보 DTO - DB 스키마 기반"""
    caregiverId: str = Field(..., description="요양보호사 ID")
    userId: str = Field(..., description="사용자 ID")
    availableTimes: Optional[str] = Field(None, description="가능 시간")
    address: Optional[str] = Field(None, description="주소")
    serviceType: Optional[str] = Field(None, description="서비스 유형")
    daysOff: Optional[str] = Field(None, description="휴무일")
    career: Optional[str] = Field(None, description="경력")
    koreanProficiency: Optional[str] = Field(None, description="한국어 실력")
    isAccompanyOuting: Optional[bool] = Field(None, description="외출 동행 가능 여부")
    selfIntroduction: Optional[str] = Field(None, description="자기소개")
    isVerified: Optional[bool] = Field(None, description="검증 여부")
    baseLocation: List[float] = Field(..., description="활동 지역 위치 (위도, 경도)")
    careerYears: int = Field(0, description="경력 년수")
    # 선호도 정보 (CaregiverPreference 테이블에서 조인)
    workDays: Optional[str] = Field(None, description="근무일")
    workArea: Optional[str] = Field(None, description="근무 지역")
    transportation: Optional[str] = Field(None, description="교통수단")
    supportedConditions: Optional[str] = Field(None, description="지원 가능 조건")
    
    @validator('baseLocation')
    def validate_base_coordinates(cls, v):
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

class MatchingRequestDTO(BaseModel):
    """매칭 요청 DTO - ServiceRequest 객체 + 요양보호사 리스트"""
    serviceRequest: ServiceRequestDTO = Field(..., description="서비스 요청 정보")
    candidateCaregivers: List[CaregiverForMatchingDTO] = Field(..., description="매칭 후보 요양보호사 목록")

class MatchedCaregiverDTO(BaseModel):
    """매칭된 요양보호사 정보 DTO"""
    caregiverId: str = Field(..., description="요양보호사 ID")
    availableTimes: Optional[str] = Field(None, description="가능 시간")
    address: Optional[str] = Field(None, description="주소")
    location: Optional[List[float]] = Field(None, description="위치 (위도, 경도)")
    matchScore: float = Field(..., description="매칭 점수")
    matchReason: str = Field(..., description="매칭 이유")
    distanceKm: Optional[float] = Field(None, description="거리 (km)")
    estimatedTravelTime: Optional[int] = Field(None, description="예상 이동 시간 (분)")
    career: Optional[str] = Field(None, description="경력")
    serviceType: Optional[str] = Field(None, description="서비스 유형")
    isVerified: Optional[bool] = Field(None, description="검증 여부")
    
    @validator('location')
    def validate_location_coordinates(cls, v):
        if v is not None:
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

class MatchingResponseDTO(BaseModel):
    """매칭 응답 DTO - 매칭된 요양보호사 리스트 (최소 1명, 최대 5명)"""
    matchedCaregivers: List[MatchedCaregiverDTO] = Field(..., description="매칭된 요양보호사 목록", min_items=1, max_items=5)
    totalMatches: int = Field(..., description="총 매칭된 요양보호사 수")
    
    @validator('matchedCaregivers')
    def validate_matched_caregivers_count(cls, v):
        if len(v) < 1:
            raise ValueError('최소 1명의 요양보호사가 매칭되어야 합니다')
        if len(v) > 5:
            raise ValueError('최대 5명까지만 매칭할 수 있습니다')
        return v