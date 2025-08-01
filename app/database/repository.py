"""
Repository 패턴 구현
데이터베이스 조회 로직을 추상화
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import List, Optional
import logging

from .models import ServiceRequestModel, CaregiverModel, UserModel
from ..entities.service_request import ServiceRequest
from ..entities.caregiver import Caregiver
from ..entities.user import User

logger = logging.getLogger(__name__)

class ServiceRequestRepository:
    """서비스 요청 Repository"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, service_request_id: str) -> Optional[ServiceRequestModel]:
        """서비스 요청 ID로 조회 (사용자 정보 포함)"""
        try:
            stmt = select(ServiceRequestModel).options(
                selectinload(ServiceRequestModel.user)
            ).where(ServiceRequestModel.service_request_id == service_request_id)
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"서비스 요청 조회 오류: {e}")
            return None
    
    async def get_pending_requests(self) -> List[ServiceRequestModel]:
        """대기 중인 서비스 요청들 조회"""
        try:
            stmt = select(ServiceRequestModel).options(
                selectinload(ServiceRequestModel.user)
            ).where(ServiceRequestModel.status == "PENDING")
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"대기 중인 서비스 요청 조회 오류: {e}")
            return []

class CaregiverRepository:
    """요양보호사 Repository"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, caregiver_id: str) -> Optional[CaregiverModel]:
        """요양보호사 ID로 조회 (사용자, 센터 정보 포함)"""
        try:
            stmt = select(CaregiverModel).options(
                selectinload(CaregiverModel.user),
                selectinload(CaregiverModel.center)
            ).where(CaregiverModel.caregiver_id == caregiver_id)
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"요양보호사 조회 오류: {e}")
            return None
    
    async def get_by_service_type(self, service_type: str) -> List[CaregiverModel]:
        """서비스 유형으로 요양보호사들 조회"""
        try:
            # JSON 필드에서 서비스 타입 검색
            stmt = select(CaregiverModel).options(
                selectinload(CaregiverModel.user),
                selectinload(CaregiverModel.center)
            ).where(
                CaregiverModel.service_types.contains([service_type])
            )
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"서비스 유형별 요양보호사 조회 오류: {e}")
            return []
    
    async def get_available_caregivers(
        self, 
        service_type: str, 
        location: List[float], 
        radius_km: float = 50.0
    ) -> List[CaregiverModel]:
        """
        매칭 가능한 요양보호사들 조회
        - 서비스 유형 일치
        - 지역 범위 내 (추후 거리 계산으로 필터링)
        """
        try:
            stmt = select(CaregiverModel).options(
                selectinload(CaregiverModel.user),
                selectinload(CaregiverModel.center)
            ).where(
                CaregiverModel.service_types.contains([service_type])
            )
            
            result = await self.db.execute(stmt)
            caregivers = result.scalars().all()
            
            # 추후 거리 계산 로직으로 필터링할 수 있음
            # 현재는 모든 매칭 가능한 요양보호사 반환
            return caregivers
            
        except Exception as e:
            logger.error(f"매칭 가능한 요양보호사 조회 오류: {e}")
            return []
    
    async def get_all_active(self) -> List[CaregiverModel]:
        """활성화된 모든 요양보호사 조회"""
        try:
            stmt = select(CaregiverModel).options(
                selectinload(CaregiverModel.user),
                selectinload(CaregiverModel.center)
            )
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"전체 요양보호사 조회 오류: {e}")
            return []

class UserRepository:
    """사용자 Repository"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: str) -> Optional[UserModel]:
        """사용자 ID로 조회"""
        try:
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"사용자 조회 오류: {e}")
            return None
    
    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """이메일로 사용자 조회"""
        try:
            stmt = select(UserModel).where(UserModel.email == email)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"이메일로 사용자 조회 오류: {e}")
            return None