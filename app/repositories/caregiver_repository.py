"""
요양보호사 데이터 리포지토리
SQLAlchemy ORM을 사용한 데이터베이스 조회 기능
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..models.matching import Caregiver, CaregiverPreference
from ..dto.matching import CaregiverForMatchingDTO
# LocationInfo 제거 - 더 이상 사용하지 않음

async def get_all_caregivers(session: AsyncSession) -> List[CaregiverForMatchingDTO]:
    """
    데이터베이스에서 모든 요양보호사 정보를 조회하여 DTO로 변환
    """
    try:
        # 요양보호사와 선호도 정보를 함께 조회
        stmt = select(Caregiver).options(
            selectinload(Caregiver.preferences)
        ).where(Caregiver.verified_status == "VERIFIED")
        
        result = await session.execute(stmt)
        caregivers = result.scalars().all()
        
        # ORM 모델을 DTO로 변환
        caregiver_dtos = []
        for caregiver in caregivers:
            # 위치 정보가 있는 경우에만 처리
            if caregiver.latitude is not None and caregiver.longitude is not None:
                caregiver_dto = CaregiverForMatchingDTO(
                    caregiverId=str(caregiver.caregiver_id),
                    userId=str(caregiver.user_id),
                    name=caregiver.name,
                    address=caregiver.address,
                    addressType=caregiver.address_type,
                    location=f"{caregiver.latitude},{caregiver.longitude}",
                    career=str(caregiver.career) if caregiver.career else None,
                    koreanProficiency=caregiver.korean_proficiency,
                    isAccompanyOuting=caregiver.is_accompany_outing,
                    selfIntroduction=caregiver.self_introduction,
                    verifiedStatus=caregiver.verified_status,
                    preferences=None  # 선호도 정보는 별도로 처리
                )
                caregiver_dtos.append(caregiver_dto)
        
        return caregiver_dtos
        
    except Exception as e:
        # 데이터베이스 조회 실패 시 빈 리스트 반환
        # 실제 운영에서는 적절한 에러 처리 필요
        return []

async def get_caregiver_by_id(session: AsyncSession, caregiver_id: str) -> Optional[CaregiverForMatchingDTO]:
    """
    특정 ID의 요極보호사 정보 조회
    """
    try:
        stmt = select(Caregiver).options(
            selectinload(Caregiver.preferences)
        ).where(
            Caregiver.caregiver_id == caregiver_id,
            Caregiver.verified_status == "VERIFIED"
        )
        
        result = await session.execute(stmt)
        caregiver = result.scalar_one_or_none()
        
        if not caregiver or caregiver.latitude is None or caregiver.longitude is None:
            return None
        
        return CaregiverForMatchingDTO(
            caregiverId=str(caregiver.c极giver_id),
            userId=str(caregiver.user_id),
            name=caregiver.name,
            address=caregiver.address,
            addressType=caregiver.address_type,
            location=f"{caregiver.latitude},{caregiver.longitude}",
            career=str(caregiver.career) if caregiver.career else None,
            koreanProficiency=caregiver.korean_proficiency,
            isAccompanyOuting=caregiver.is_accompany_outing,
            selfIntroduction=caregiver.self_introduction,
            verifiedStatus=caregiver.verified_status,
            preferences=None
        )
        
    except Exception as e:
        return None