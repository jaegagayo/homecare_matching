"""
요양보호사 데이터 리포지토리
SQLAlchemy ORM을 사용한 데이터베이스 조회 기능
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..models.matching import Caregiver, CaregiverPreference, User
from ..dto.matching import CaregiverForMatchingDTO
# LocationInfo 제거 - 더 이상 사용하지 않음

async def get_all_caregivers(session: AsyncSession) -> List[CaregiverForMatchingDTO]:
    """
    데이터베이스에서 모든 요양보호사 정보를 조회하여 DTO로 변환
    caregiver와 caregiver_preference 테이블을 명시적으로 조인하여 모든 필요한 정보를 가져옴
    """
    try:
        # 요양보호사와 선호도 정보를 함께 조회
        stmt = (
            select(Caregiver, CaregiverPreference, User)
            .outerjoin(CaregiverPreference, CaregiverPreference.caregiver_id == Caregiver.id)
            .join(User, User.id == Caregiver.user_id)
            .where(Caregiver.verified_status == "APPROVED")
        )
        
        result = await session.execute(stmt)
        rows = result.all()
        
        # ORM 모델을 DTO로 변환
        caregiver_dtos = []
        for caregiver, pref, user in rows:
            # 위치 정보가 있는 경우에만 처리
            if pref.latitude is not None and pref.longitude is not None:
                caregiver_dto = CaregiverForMatchingDTO(
                    caregiverId=str(caregiver.caregiver_id),
                    userId=str(user.user_id),
                    name=user.name if user else None,
                    address=pref.work_area if pref else None,
                    addressType=pref.address_type if pref else None,
                    latitude = pref.latitude,
                    longitude = pref.longitude,
                    career=str(caregiver.career) if caregiver.career else None,
                    koreanProficiency=caregiver.korean_proficiency,
                    isAccompanyOuting=caregiver.is_accompany_outing,
                    selfIntroduction=caregiver.self_introduction,
                    verifiedStatus=caregiver.verified_status,
                    # 추가 정보들을 preferences에서 안전하게 가져와서 설정
                    workStartTime=str(preference.work_start_time) if preference and preference.work_start_time else None,
                    workEndTime=str(preference.work_end_time) if preference and preference.work_end_time else None,
                    workArea=preference.work_area if preference else None,
                    serviceType=preference.service_types if preference else None,
                    baseLocation=preference.location if preference else None,  # 동일한 location 사용
                    careerYears=caregiver.career if caregiver.career else None,
                    transportation=preference.transportation if preference else None,
                    preferences=None  # 필요시 별도로 처리
                )
                caregiver_dtos.append(caregiver_dto)
        
        return caregiver_dtos
        
    except Exception as e:
        # 데이터베이스 조회 실패 시 빈 리스트 반환
        # 실제 운영에서는 적절한 에러 처리 필요
        print(f"데이터베이스 조회 오류: {str(e)}")  # 디버깅을 위한 로그
        return []

async def get_caregiver_by_id(session: AsyncSession, caregiver_id: str) -> Optional[CaregiverForMatchingDTO]:
    """
    특정 ID의 요양보호사 정보 조회
    """
    try:
    
        stmt = (
            select(Caregiver, CaregiverPreference, User)
            .outerjoin(CaregiverPreference, CaregiverPreference.caregiver_id == Caregiver.id)
            .join(User, User.id == Caregiver.user_id)
            .where(Caregiver.caregiver_id == caregiver_id, Caregiver.verified_status == "APPROVED")
        )

        result = await session.execute(stmt)
        row = result.one_or_none()
        
        if row is None:
            return None

        caregiver, pref, user = row
        
        if pref.latitude is None or pref.longitude is None:
            return None
        
        return CaregiverForMatchingDTO(
            caregiverId=str(caregiver.caregiver_id),
            userId=str(caregiver.user_id),
            name=user.name if user else None,
            address=pref.work_area if pref else None,
            addressType=pref.address_type if pref else None,
            latitude = pref.latitude,
            longitude = pref.longitude,
            career=str(caregiver.career) if caregiver.career else None,
            koreanProficiency=caregiver.korean_proficiency,
            isAccompanyOuting=caregiver.is_accompany_outing,
            selfIntroduction=caregiver.self_introduction,
            verifiedStatus=caregiver.verified_status,
            preferences=None
        )
        
    except Exception as e:
        return None
