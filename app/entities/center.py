from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re
from .user import User

class Center(BaseModel):
    id: Optional[int] = Field(None, description="DB 자동생성 ID")
    centerId: str = Field(..., description="센터 ID (UUID)")
    user: Optional[User] = Field(None, description="연결된 사용자")
    name: Optional[str] = Field(None, description="센터 이름")
    center_address: Optional[str] = Field(None, description="센터 주소")
    center_location: Optional[List[float]] = Field(None, description="센터 위치 (위도, 경도)")
    contact_number: Optional[str] = Field(None, description="센터 연락처")
    
    @validator('centerId')
    def validate_uuid_format(cls, v):
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('UUID 형식이 올바르지 않습니다')
        return v
    
    @validator('center_location')
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
    
    @validator('contact_number')
    def validate_contact_number(cls, v):
        if v:
            # 전화번호 형식 검증
            phone_pattern = r'^0\d{1,2}-?\d{3,4}-?\d{4}$'
            if not re.match(phone_pattern, v):
                raise ValueError('올바른 전화번호 형식이 아닙니다')
        return v