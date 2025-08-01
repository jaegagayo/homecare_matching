from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re
from .user import User
from .center import Center
from .base import ServiceType, DayOfWeek

class Caregiver(BaseModel):
    id: Optional[int] = Field(None, description="DB 자동생성 ID")
    caregiverId: str = Field(..., description="요양보호사 ID (UUID)")
    user: Optional[User] = Field(None, description="연결된 사용자")
    center: Optional[Center] = Field(None, description="연결된 센터")
    availableStartTime: Optional[str] = Field(None, description="근무 시간 (HH:MM)")
    availableEndTime: Optional[str] = Field(None, description="근무 종료 시간 (HH:MM)")
    address: Optional[str] = Field(None, description="주소")
    location: Optional[List[float]] = Field(None, description="위치 (위도, 경도)")
    serviceTypes: List[ServiceType] = Field(default=[], description="서비스 유형들")
    daysOff: List[DayOfWeek] = Field(default=[], description="휴무일들")
    
    @validator('caregiverId')
    def validate_uuid_format(cls, v):
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('UUID 형식이 올바르지 않습니다')
        return v
    
    @validator('location')
    def validate_coordinates(cls, v):
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
    
    @validator('availableStartTime', 'availableEndTime')
    def validate_time_format(cls, v):
        if v and not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('시간은 HH:MM 형식이어야 합니다')
        return v