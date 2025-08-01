"""
데이터 조회 서비스
DTO를 통해 필요한 Entity 데이터를 데이터베이스에서 조회
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from ..dto.matching import MatchingRequestDTO
from ..database.repository import ServiceRequestRepository, CaregiverRepository
from ..database.models import ServiceRequestModel, CaregiverModel

logger = logging.getLogger(__name__)

class MatchingDataService:
    """매칭을 위한 데이터 조회 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.service_request_repo = ServiceRequestRepository(db)
        self.caregiver_repo = CaregiverRepository(db)
    
    async def get_consumer_data(self, request_dto: MatchingRequestDTO) -> Optional[ServiceRequestModel]:
        """
        DTO에서 서비스 요청 ID를 사용하여 전체 수요자 데이터 조회
        
        Args:
            request_dto: 매칭 요청 DTO
            
        Returns:
            ServiceRequestModel: 서비스 요청 전체 정보 (사용자 정보 포함)
        """
        try:
            service_request = await self.service_request_repo.get_by_id(
                request_dto.serviceRequestId
            )
            
            if not service_request:
                logger.warning(f"서비스 요청을 찾을 수 없음: {request_dto.serviceRequestId}")
                return None
            
            logger.info(f"수요자 데이터 조회 완료: {service_request.service_request_id}")
            return service_request
            
        except Exception as e:
            logger.error(f"수요자 데이터 조회 오류: {e}")
            return None
    
    async def get_available_caregivers(self, request_dto: MatchingRequestDTO) -> List[CaregiverModel]:
        """
        DTO의 서비스 타입과 위치 정보를 사용하여 매칭 가능한 요양보호사 목록 조회
        
        Args:
            request_dto: 매칭 요청 DTO
            
        Returns:
            List[CaregiverModel]: 매칭 가능한 요양보호사 목록
        """
        try:
            # 서비스 타입에 따른 요양보호사 조회
            caregivers = await self.caregiver_repo.get_available_caregivers(
                service_type=request_dto.serviceType,
                location=request_dto.location,
                radius_km=50.0  # 50km 반경
            )
            
            logger.info(f"매칭 가능한 요양보호사 조회 완료: {len(caregivers)}명")
            return caregivers
            
        except Exception as e:
            logger.error(f"요양보호사 데이터 조회 오류: {e}")
            return []
    
    async def get_specific_caregivers(self, caregiver_ids: List[str]) -> List[CaregiverModel]:
        """
        특정 요양보호사 ID 목록으로 조회
        
        Args:
            caregiver_ids: 요양보호사 ID 목록
            
        Returns:
            List[CaregiverModel]: 조회된 요양보호사 목록
        """
        try:
            caregivers = []
            for caregiver_id in caregiver_ids:
                caregiver = await self.caregiver_repo.get_by_id(caregiver_id)
                if caregiver:
                    caregivers.append(caregiver)
                else:
                    logger.warning(f"요양보호사를 찾을 수 없음: {caregiver_id}")
            
            logger.info(f"특정 요양보호사 조회 완료: {len(caregivers)}명")
            return caregivers
            
        except Exception as e:
            logger.error(f"특정 요양보호사 조회 오류: {e}")
            return []

class DataValidationService:
    """데이터 검증 서비스"""
    
    @staticmethod
    def validate_service_request_data(service_request: ServiceRequestModel) -> bool:
        """
        서비스 요청 데이터의 완전성 검증
        
        Args:
            service_request: 서비스 요청 모델
            
        Returns:
            bool: 데이터가 유효한지 여부
        """
        try:
            # 필수 필드 검사
            if not service_request.service_request_id:
                logger.error("서비스 요청 ID가 없음")
                return False
            
            if not service_request.location or len(service_request.location) != 2:
                logger.error("위치 정보가 유효하지 않음")
                return False
            
            if not service_request.service_type:
                logger.error("서비스 유형이 없음")
                return False
            
            if not service_request.requested_days:
                logger.error("요청 요일이 없음")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"서비스 요청 데이터 검증 오류: {e}")
            return False
    
    @staticmethod
    def validate_caregiver_data(caregiver: CaregiverModel) -> bool:
        """
        요양보호사 데이터의 완전성 검증
        
        Args:
            caregiver: 요양보호사 모델
            
        Returns:
            bool: 데이터가 유효한지 여부
        """
        try:
            # 필수 필드 검사
            if not caregiver.caregiver_id:
                logger.error("요양보호사 ID가 없음")
                return False
            
            if not caregiver.location or len(caregiver.location) != 2:
                logger.error("요양보호사 위치 정보가 유효하지 않음")
                return False
            
            if not caregiver.service_types:
                logger.error("서비스 유형 정보가 없음")
                return False
            
            if not caregiver.available_start_time or not caregiver.available_end_time:
                logger.error("근무 시간 정보가 없음")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"요양보호사 데이터 검증 오류: {e}")
            return False