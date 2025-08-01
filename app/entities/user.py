from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime
import re
from .base import UserRole

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