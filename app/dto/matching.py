from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MatchingRequestDTO(BaseModel):
    serviceRequestId: str = Field(..., description="서비스 요청 ID")
    location: str = Field(..., min_length=1, description="서비스 요청 위치(주소)")
    preferred_time_start: Optional[datetime] = Field(None, description="서비스 시작 시간")
    preferred_time_end: Optional[datetime] = Field(None, description="서비스 종료 시간")
    serviceType: str = Field(..., description="요청하는 요양서비스 유형")
    # TODO : 성격 정보는 MVP 단계에서 미구현
    # personalityType: str = Field(..., description="성격 정보")
    requestedDays: List[int] = Field(..., description="요청 요일들")

class MatchingResponseDTO(BaseModel):
    caregiverId: str = Field(..., description="요양보호사 ID")
    availableStartTime: Optional[str] = Field(None, description="근무 시작 시간")
    availableEndTime: Optional[str] = Field(None, description="근무 종료 시간")
    address: Optional[str] = Field(None, description="주소")