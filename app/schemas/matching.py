from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from datetime import datetime, date
from enum import Enum
import re

# Enum 정의
class UserRole(str, Enum):
    ROLE_CONSUMER = "ROLE_CONSUMER"
    ROLE_CAREGIVER = "ROLE_CAREGIVER"
    ROLE_CENTER = "ROLE_CENTER"
    ROLE_ADMIN = "ROLE_ADMIN"

class ServiceType(str, Enum):
    VISITING_CARE = "방문요양"
    VISITING_BATH = "방문목욕"
    VISITING_NURSING = "방문간호"
    DAY_NIGHT_CARE = "주야간보호"
    RESPITE_CARE = "단기보호"

class ServiceRequestStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"

class DayOfWeek(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

# TODO : 성격 유형 추가 예정
# class PersonalityType(str, Enum):

# 유저 스키마
class User(BaseModel):
    id: Optional[int] = Field(None, description="DB 자동생성 ID")
    userId: str = Field(..., description="유저 ID (UUID)")
    name: str = Field(..., min_length=1, description="이름")
    email: EmailStr = Field(..., description="이메일")
    password: Optional[str] = Field(None, description="패스워드")
    phone: str = Field(..., description="전화번호")
    birthDate: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)")
    userRole: UserRole = Field(..., description="사용자 역할")
    createdAt: Optional[datetime] = Field(None, description="생성 시간")
    
    @validator('userId')
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
    
    @validator('birthDate')
    def validate_birth_date(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('생년월일은 YYYY-MM-DD 형식이어야 합니다')
        return v

# 센터 스키마
class Center(BaseModel):
    id: Optional[int] = Field(None, description="DB 자동생성 ID")
    centerId: str = Field(..., description="센터 ID (UUID)")
    user: Optional[User] = Field(None, description="연결된 사용자")
    name: Optional[str] = Field(None, description="센터 이름")
    center_address: Optional[str] = Field(None, description="센터 주소")
    contact_number: Optional[str] = Field(None, description="센터 연락처")
    
    @validator('centerId')
    def validate_uuid_format(cls, v):
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('UUID 형식이 올바르지 않습니다')
        return v
    
    @validator('contact_number')
    def validate_contact_number(cls, v):
        if v:
            # 전화번호 형식 검증
            phone_pattern = r'^0\d{1,2}-?\d{3,4}-?\d{4}$'
            if not re.match(phone_pattern, v):
                raise ValueError('올바른 전화번호 형식이 아닙니다')
        return v

# 요양보호사 스키마
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

# 서비스 요청 스키마
class ServiceRequest(BaseModel):
    id: Optional[int] = Field(None, description="DB 자동생성 ID")
    serviceRequestId: str = Field(..., description="서비스 요청 ID (UUID)")
    user: Optional[User] = Field(None, description="연결된 사용자")
    location: str = Field(..., min_length=1, description="서비스 요청 위치")
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
    
    @validator('requestedDays')
    def validate_requested_days(cls, v):
        if v:
            for day in v:
                if not isinstance(day, int) or day < 1 or day > 7:
                    raise ValueError('요청일은 1-7 사이의 정수여야 합니다 (1=월, 7=일)')
        return v

# === 매칭 API용 DTO ===
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