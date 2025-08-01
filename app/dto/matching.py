from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date

class ServiceRequestDTO(BaseModel):
    """서비스 요청 정보 DTO"""
    serviceRequestId: str = Field(..., description="서비스 요청 ID")
    address: str = Field(..., description="서비스 요청 주소")
    location: List[float] = Field(..., description="서비스 요청 위치 (위도, 경도)")
    preferred_time_start: Optional[datetime] = Field(None, description="서비스 시작 시간")
    preferred_time_end: Optional[datetime] = Field(None, description="서비스 종료 시간")
    serviceType: str = Field(..., description="요청하는 요양서비스 유형")
    requestedDays: List[date] = Field(..., description="요청 일들")
    # TODO : 성격 정보는 MVP 단계에서 미구현
    # personalityType: str = Field(..., description="성격 정보")
    
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
    
    @validator('requestedDays')
    def validate_requested_days(cls, v):
        if not v:
            raise ValueError('요청 일들이 비어있습니다')
        
        # 중복 날짜 제거 및 정렬
        unique_dates = sorted(list(set(v)))
        
        # 과거 날짜 확인 (선택적 - 필요에 따라 주석 해제)
        # today = date.today()
        # past_dates = [d for d in unique_dates if d < today]
        # if past_dates:
        #     raise ValueError(f'과거 날짜는 요청할 수 없습니다: {past_dates}')
        
        return unique_dates

class CaregiverForMatchingDTO(BaseModel):
    """매칭용 요양보호사 정보 DTO"""
    caregiverId: str = Field(..., description="요양보호사 ID")
    serviceType: str = Field(..., description="서비스 유형")
    closedDays: str = Field(..., description="휴무일들 (콤마로 구분)")
    availableStartTime: str = Field(..., description="근무 시작 시간")
    availableEndTime: str = Field(..., description="근무 종료 시간")
    baseAddress: str = Field(..., description="활동 지역 주소")
    baseLocation: List[float] = Field(..., description="활동 지역 위치 (위도, 경도)")
    personalityType: str = Field(..., description="성격 유형")
    careerYears: int = Field(0, description="경력 년수")
    
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
    availableStartTime: Optional[str] = Field(None, description="근무 시작 시간")
    availableEndTime: Optional[str] = Field(None, description="근무 종료 시간")
    address: Optional[str] = Field(None, description="주소")
    location: Optional[List[float]] = Field(None, description="위치 (위도, 경도)")
    matchScore: float = Field(..., description="매칭 점수")
    matchReason: str = Field(..., description="매칭 이유")
    
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