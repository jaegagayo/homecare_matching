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
    availableStartTime: Optional[str] = Field(None, description="근무 시작 시간 (HH:MM)")
    availableEndTime: Optional[str] = Field(None, description="근무 종료 시간 (HH:MM)")
    address: Optional[str] = Field(None, description="주소")
    serviceTypes: List[ServiceType] = Field(default=[], description="서비스 유형들")
    daysOff: List[DayOfWeek] = Field(default=[], description="휴무일들")
    
    @validator('caregiverId')
    def validate_uuid_format(cls, v):
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('UUID 형식이 올바르지 않습니다')
        return v
    
    @validator('availableStartTime', 'availableEndTime')
    def validate_time_format(cls, v):
        if v and not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('시간은 HH:MM 형식이어야 합니다')
        return v