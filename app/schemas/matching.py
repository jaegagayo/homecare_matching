from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import re

# Enum 정의
class UserRole(str, Enum):
    CARE_GIVER = "CARE_GIVER"
    CENTER = "CENTER" 
    CLIENT = "CLIENT"

class ServiceType(str, Enum):
    HOME_CARE = "방문요양"
    HOME_BATH = "방문목욕"
    HOME_NURSING = "방문간호"
    COMPANION = "동행서비스"

class RequestStatus(str, Enum):
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PersonalityType(str, Enum):
    GENTLE = "온순함"
    ACTIVE = "활발함"
    CALM = "차분함"
    CHEERFUL = "밝음"

# 시간 범위 스키마 (개선)
class TimeRange(BaseModel):
    start: str = Field(..., description="시작 시간 (HH:MM 형식)")
    end: str = Field(..., description="종료 시간 (HH:MM 형식)")
    
    @validator('start', 'end')
    def validate_time_format(cls, v):
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('시간은 HH:MM 형식이어야 합니다 (예: 09:00)')
        return v
    
    @validator('end')
    def validate_end_after_start(cls, v, values):
        if 'start' in values:
            start_time = values['start']
            if v <= start_time:
                raise ValueError('종료 시간은 시작 시간보다 뒤여야 합니다')
        return v

# 요양보호사 프로필 스키마 (개선)
class CaregiverProfile(BaseModel):
    caregiver_id: str = Field(..., description="요양보호사 ID (UUID)")
    user_id: str = Field(..., description="유저 ID (UUID)")
    center_id: str = Field(..., description="센터 ID (UUID)")
    career_years: int = Field(..., ge=0, description="경력 연차 (0 이상)")
    available_times: TimeRange = Field(..., description="근무 가능 시간")
    base_location: str = Field(..., min_length=1, description="거주/출발 위치")
    personality_type: PersonalityType = Field(..., description="성격 정보")
    service_type: ServiceType = Field(..., description="서비스 유형")
    closed_days: str = Field(..., description="휴무 요일 (1=월, 2=화, ..., 7=일) 예: '1,3,5'")
    
    @validator('caregiver_id', 'user_id', 'center_id')
    def validate_uuid_format(cls, v):
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('UUID 형식이 올바르지 않습니다')
        return v
    
    @validator('closed_days')
    def validate_closed_days(cls, v):
        if v:  # 빈 문자열이 아닌 경우만 검증
            days = v.split(',')
            for day in days:
                day = day.strip()
                if not day.isdigit() or int(day) < 1 or int(day) > 7:
                    raise ValueError('휴무일은 1-7 사이의 숫자여야 합니다 (1=월, 7=일)')
        return v

# 수요자 신청 정보 스키마 (개선)
class ServiceRequest(BaseModel):
    serviceRequest_id: str = Field(..., description="수요자 신청정보 ID (UUID)")
    user_id: str = Field(..., description="유저 ID (UUID)")
    location: str = Field(..., min_length=1, description="서비스 요청 위치")
    preferred_time: TimeRange = Field(..., description="선호 시간대")
    service_type: ServiceType = Field(..., description="서비스 유형")
    status: RequestStatus = Field(..., description="신청 상태")
    personality_type: PersonalityType = Field(..., description="성격 정보")
    requested_days: str = Field(..., description="서비스 요청 요일 (1=월, 2=화, ..., 7=일)")
    
    @validator('serviceRequest_id', 'user_id')
    def validate_uuid_format(cls, v):
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('UUID 형식이 올바르지 않습니다')
        return v

# 유저 기본 정보 스키마 (개선)
class User(BaseModel):
    user_id: str = Field(..., description="유저 ID (UUID)")
    name: str = Field(..., min_length=1, max_length=50, description="이름")
    email: EmailStr = Field(..., description="이메일")
    phone: str = Field(..., description="전화번호")
    role: UserRole = Field(..., description="역할")
    
    @validator('user_id')
    def validate_uuid_format(cls, v):
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('UUID 형식이 올바르지 않습니다')
        return v
    
    @validator('phone')
    def validate_phone_format(cls, v):
        # 한국 전화번호 형식 검증 (010-1234-5678 또는 01012345678)
        phone_pattern = r'^01[016789]-?\d{3,4}-?\d{4}$'
        if not re.match(phone_pattern, v):
            raise ValueError('올바른 전화번호 형식이 아닙니다')
        return v

# === 매칭 API용 DTO (개선) ===
class ConsumerForMatching(BaseModel):
    serviceRequest_id: str = Field(..., description="서비스 요청 ID")
    user_id: str = Field(..., description="유저 ID")
    location: str = Field(..., min_length=1, description="서비스 위치")
    preferred_time: TimeRange = Field(..., description="선호 시간대")
    service_type: ServiceType = Field(..., description="서비스 유형")
    personality_type: PersonalityType = Field(..., description="성격 정보")
    requested_days: str = Field(..., description="요청 요일들")

class CaregiverForMatching(BaseModel):
    caregiver_id: str = Field(..., description="요양보호사 ID")
    user_id: str = Field(..., description="유저 ID")
    center_id: str = Field(..., description="센터 ID")
    career_years: int = Field(..., ge=0, description="경력 연차")
    available_times: TimeRange = Field(..., description="근무 가능 시간")
    base_location: str = Field(..., min_length=1, description="거주/출발 위치")
    personality_type: PersonalityType = Field(..., description="성격 정보")
    service_type: ServiceType = Field(..., description="서비스 유형")
    closed_days: str = Field(..., description="휴무일")

# 매칭 요청 DTO
class MatchingRequestDTO(BaseModel):
    consumer: ConsumerForMatching = Field(..., description="수요자 정보")
    caregivers: List[CaregiverForMatching] = Field(..., min_items=1, description="요양보호사 리스트")

# 매칭된 요양보호사 결과 (개선)
class MatchedCaregiver(BaseModel):
    caregiver_id: str = Field(..., description="매칭된 요양보호사 ID")
    match_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="매칭 점수 (0-100)")
    reason: Optional[str] = Field(None, description="매칭 이유")

# 매칭 응답 DTO (개선)
class MatchingResponseDTO(BaseModel):
    matched_caregivers: List[MatchedCaregiver] = Field(..., description="매칭된 요양보호사 리스트")
    total_matches: int = Field(..., ge=0, description="총 매칭 수")
    status: str = Field(default="success", description="처리 상태")
    message: Optional[str] = Field(None, description="결과 메시지")
