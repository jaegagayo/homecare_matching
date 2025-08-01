from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re
from .user import User
from .base import ServiceRequestStatus

class ServiceRequest(BaseModel):
    id: Optional[int] = Field(None, description="DB 자동생성 ID")
    serviceRequestId: str = Field(..., description="서비스 요청 ID (UUID)")
    user: Optional[User] = Field(None, description="연결된 사용자")
    address: str = Field(..., description="서비스 요청 주소")
    location: List[float] = Field(..., description="서비스 요청 위치 (위도, 경도)")
    preferred_time_start: Optional[datetime] = Field(None, description="선호 시작 시간")
    preferred_time_end: Optional[datetime] = Field(None, description="선호 종료 시간")
    serviceType: str = Field(..., description="서비스 유형 (String)")
    status: ServiceRequestStatus = Field(..., description="신청 상태")
    personalityType: str = Field(..., description="성격 정보 (String)")
    requestedDays: List[int] = Field(..., description="서비스 요청 요일 (1=월, 2=화, ..., 7=일)")
    additionalInformation: Optional[str] = Field(None, description="추가 정보")
    
    @validator('serviceRequestId')
    def validate_uuid_format(cls, v):
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('UUID 형식이 올바르지 않습니다')
        return v
    
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
    
    @validator('requestedDays')
    def validate_requested_days(cls, v):
        if v:
            for day in v:
                if not isinstance(day, int) or day < 1 or day > 7:
                    raise ValueError('요청일은 1-7 사이의 정수여야 합니다 (1=월, 7=일)')
        return v