from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..entities.base import ServiceType, DayOfWeek

class MatchingRequestDTO(BaseModel):
    serviceRequestId: str = Field(..., description="서비스 요청 ID")
    location: str = Field(..., min_length=1, description="서비스 위치")
    preferred_time_start: Optional[datetime] = Field(None, description="선호 시작 시간")
    preferred_time_end: Optional[datetime] = Field(None, description="선호 종료 시간")
    serviceType: str = Field(..., description="서비스 유형")
    personalityType: str = Field(..., description="성격 정보")
    requestedDays: List[int] = Field(..., description="요청 요일들")
    additionalInformation: Optional[str] = Field(None, description="추가 정보")

class MatchingResponseDTO(BaseModel):
    caregiverId: str = Field(..., description="요양보호사 ID")
    availableStartTime: Optional[str] = Field(None, description="근무 시작 시간")
    availableEndTime: Optional[str] = Field(None, description="근무 종료 시간")
    address: Optional[str] = Field(None, description="주소")
    serviceTypes: List[ServiceType] = Field(default=[], description="서비스 유형들")
    daysOff: List[DayOfWeek] = Field(default=[], description="휴무일들")