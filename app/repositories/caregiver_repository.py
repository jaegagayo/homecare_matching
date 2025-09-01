"""
요양보호사 데이터 리포지토리
SQLAlchemy ORM을 사용한 데이터베이스 조회 기능
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.matching import Caregiver, CaregiverPreference
from ..dto.matching import CaregiverForMatchingDTO
# LocationInfo 제거 - 더 이상 사용하지 않음

async def get_all_caregivers(session: AsyncSession) -> List[CaregiverForMatchingDTO]:
    """
    데이터베이스에서 모든 요양보호사 정보를 조회하여 DTO로 변환
    caregiver와 caregiver_preference 테이블을 명시적으로 조인하여 모든 필요한 정보를 가져옴
    """
    try:
        # caregiver와 caregiver_preference를 명시적으로 조인
        stmt = select(Caregiver, CaregiverPreference).join(
            CaregiverPreference, Caregiver.id == CaregiverPreference.caregiver_id, isouter=True
        ).where(Caregiver.verified_status == "APPROVED")
        
        result = await session.execute(stmt)
        rows = result.all()
        
        # ORM 모델을 DTO로 변환
        caregiver_dtos = []
        for caregiver, preference in rows:
            # preference에서 위치 정보가 있는 경우만 매칭 대상으로 포함
            if preference and preference.location:
                # CaregiverForMatchingDTO에 필요한 모든 정보를 안전하게 설정
                caregiver_dto = CaregiverForMatchingDTO(
                    caregiverId=str(caregiver.caregiver_id),
                    userId=str(caregiver.user_id),
                    name=None,  # caregiver 테이블에 name 필드가 없음
                    address=caregiver.address,
                    addressType=preference.address_type if preference else None,
                    location=preference.location if preference else None,
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

# get_caregiver_by_id 메서드 제거됨 - 더 이상 사용하지 않음