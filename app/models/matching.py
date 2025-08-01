from pydantic import BaseModel, Field
from ..entities.base import ServiceType, PersonalityType

class TimeRange(BaseModel):
    start: str = Field(..., description="시작 시간 (HH:MM)")
    end: str = Field(..., description="종료 시간 (HH:MM)")

class ConsumerForMatching(BaseModel):
    service_type: ServiceType = Field(..., description="서비스 유형")
    requested_days: str = Field(..., description="요청 요일들 (콤마로 구분)")
    preferred_time: TimeRange = Field(..., description="선호 시간대")
    location: str = Field(..., description="서비스 위치")
    personality_type: PersonalityType = Field(..., description="성격 유형")

class CaregiverForMatching(BaseModel):
    caregiver_id: str = Field(..., description="요양보호사 ID")
    service_type: ServiceType = Field(..., description="서비스 유형")
    closed_days: str = Field(..., description="휴무일들 (콤마로 구분)")
    available_times: TimeRange = Field(..., description="근무 가능 시간")
    base_location: str = Field(..., description="활동 지역")
    personality_type: PersonalityType = Field(..., description="성격 유형")
    career_years: int = Field(0, description="경력 년수")

class MatchedCaregiver(BaseModel):
    caregiver_id: str = Field(..., description="요양보호사 ID")
    match_score: float = Field(..., description="매칭 점수")
    reason: str = Field(..., description="매칭 이유")