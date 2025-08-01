from pydantic import BaseModel, Field, validator
from typing import List

class CaregiverForMatching(BaseModel):
    caregiver_id: str = Field(..., description="요양보호사 ID")
    base_location: List[float] = Field(..., description="활동 지역 위치 (위도, 경도)")
    career_years: int = Field(0, description="경력 년수")
    
    @validator('base_location')
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

class MatchedCaregiver(BaseModel):
    caregiver_id: str = Field(..., description="요양보호사 ID")
    match_score: float = Field(..., description="매칭 점수")
    reason: str = Field(..., description="매칭 이유")