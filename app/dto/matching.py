from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class MatchingRequestDTO(BaseModel):
    serviceRequestId: str = Field(..., description="서비스 요청 ID")
    address: str = Field(..., description="서비스 요청 주소")
    location: List[float] = Field(..., description="서비스 요청 위치 (위도, 경도)")
    preferred_time_start: Optional[datetime] = Field(None, description="서비스 시작 시간")
    preferred_time_end: Optional[datetime] = Field(None, description="서비스 종료 시간")
    serviceType: str = Field(..., description="요청하는 요양서비스 유형")
    # TODO : 성격 정보는 MVP 단계에서 미구현
    # personalityType: str = Field(..., description="성격 정보")
    requestedDays: List[int] = Field(..., description="요청 요일들")
    
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

class MatchingResponseDTO(BaseModel):
    caregiverId: str = Field(..., description="요양보호사 ID")
    availableStartTime: Optional[str] = Field(None, description="근무 시작 시간")
    availableEndTime: Optional[str] = Field(None, description="근무 종료 시간")
    address: Optional[str] = Field(None, description="주소")
    location: Optional[List[float]] = Field(None, description="위치 (위도, 경도)")
    
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