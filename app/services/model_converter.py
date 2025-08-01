"""
모델 변환 서비스
SQLAlchemy Entity를 Matching 모델로 변환
"""

from typing import List, Optional
from datetime import datetime
import logging

from ..database.models import ServiceRequestModel, CaregiverModel
from ..models.matching import ConsumerForMatching, CaregiverForMatching, TimeRange
from ..entities.base import ServiceType, PersonalityType, DayOfWeek

logger = logging.getLogger(__name__)

class ModelConverter:
    """Entity와 Matching 모델 간 변환 서비스"""
    
    @staticmethod
    def service_request_to_consumer(service_request: ServiceRequestModel) -> Optional[ConsumerForMatching]:
        """
        ServiceRequestModel을 ConsumerForMatching으로 변환
        
        Args:
            service_request: 데이터베이스에서 조회한 서비스 요청
            
        Returns:
            ConsumerForMatching: 매칭용 수요자 모델
        """
        try:
            # 요청 요일을 문자열로 변환 (1=월, 2=화, ..., 7=일)
            day_mapping = {1: "월", 2: "화", 3: "수", 4: "목", 5: "금", 6: "토", 7: "일"}
            requested_days_str = ",".join([
                day_mapping.get(day, str(day)) for day in service_request.requested_days
            ])
            
            # 선호 시간 설정
            preferred_time = ModelConverter._extract_preferred_time(
                service_request.preferred_time_start,
                service_request.preferred_time_end
            )
            
            # 서비스 유형 변환
            service_type = ModelConverter._convert_service_type_string_to_enum(
                service_request.service_type
            )
            
            # 성격 유형 변환
            personality_type = ModelConverter._convert_personality_type_string_to_enum(
                service_request.personality_type
            )
            
            consumer = ConsumerForMatching(
                service_type=service_type,
                requested_days=requested_days_str,
                preferred_time=preferred_time,
                address=service_request.address,
                location=service_request.location,
                personality_type=personality_type
            )
            
            logger.info(f"수요자 변환 완료: {service_request.service_request_id}")
            return consumer
            
        except Exception as e:
            logger.error(f"수요자 모델 변환 오류: {e}")
            return None
    
    @staticmethod
    def caregiver_to_matching_model(caregiver: CaregiverModel) -> Optional[CaregiverForMatching]:
        """
        CaregiverModel을 CaregiverForMatching으로 변환
        
        Args:
            caregiver: 데이터베이스에서 조회한 요양보호사
            
        Returns:
            CaregiverForMatching: 매칭용 요양보호사 모델
        """
        try:
            # 휴무일 변환 (DayOfWeek enum을 문자열로)
            closed_days_str = ModelConverter._convert_days_off_to_string(caregiver.days_off)
            
            # 근무 시간 설정
            available_times = TimeRange(
                start=caregiver.available_start_time or "09:00",
                end=caregiver.available_end_time or "18:00"
            )
            
            # 서비스 유형 (첫 번째 서비스 유형 사용)
            service_type = ModelConverter._get_primary_service_type(caregiver.service_types)
            
            # 성격 유형 (기본값 사용)
            personality_type = caregiver.personality_type or PersonalityType.GENTLE
            
            caregiver_matching = CaregiverForMatching(
                caregiver_id=caregiver.caregiver_id,
                service_type=service_type,
                closed_days=closed_days_str,
                available_times=available_times,
                base_address=caregiver.address or "",
                base_location=caregiver.location or [0.0, 0.0],
                personality_type=personality_type,
                career_years=caregiver.career_years or 0
            )
            
            logger.info(f"요양보호사 변환 완료: {caregiver.caregiver_id}")
            return caregiver_matching
            
        except Exception as e:
            logger.error(f"요양보호사 모델 변환 오류: {e}")
            return None
    
    @staticmethod
    def caregivers_to_matching_models(caregivers: List[CaregiverModel]) -> List[CaregiverForMatching]:
        """
        여러 요양보호사를 한 번에 변환
        
        Args:
            caregivers: 요양보호사 목록
            
        Returns:
            List[CaregiverForMatching]: 변환된 매칭용 요양보호사 목록
        """
        matching_caregivers = []
        for caregiver in caregivers:
            matching_caregiver = ModelConverter.caregiver_to_matching_model(caregiver)
            if matching_caregiver:
                matching_caregivers.append(matching_caregiver)
        
        logger.info(f"요양보호사 일괄 변환 완료: {len(matching_caregivers)}명")
        return matching_caregivers
    
    @staticmethod
    def _extract_preferred_time(start_time: Optional[datetime], end_time: Optional[datetime]) -> TimeRange:
        """
        datetime 객체에서 시간 문자열 추출
        
        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            
        Returns:
            TimeRange: 시간 범위
        """
        try:
            if start_time and end_time:
                start_str = start_time.strftime("%H:%M")
                end_str = end_time.strftime("%H:%M")
                return TimeRange(start=start_str, end=end_str)
            else:
                # 기본 시간 설정
                return TimeRange(start="09:00", end="18:00")
        except Exception as e:
            logger.warning(f"시간 추출 오류: {e}, 기본값 사용")
            return TimeRange(start="09:00", end="18:00")
    
    @staticmethod
    def _convert_service_type_string_to_enum(service_type_str: str) -> ServiceType:
        """
        서비스 유형 문자열을 enum으로 변환
        
        Args:
            service_type_str: 서비스 유형 문자열
            
        Returns:
            ServiceType: 서비스 유형 enum
        """
        try:
            # 문자열과 enum 매핑
            for service_type in ServiceType:
                if service_type.value == service_type_str:
                    return service_type
            
            # 매칭되지 않으면 기본값
            logger.warning(f"알 수 없는 서비스 유형: {service_type_str}, 기본값 사용")
            return ServiceType.VISITING_CARE
        except Exception as e:
            logger.warning(f"서비스 유형 변환 오류: {e}, 기본값 사용")
            return ServiceType.VISITING_CARE
    
    @staticmethod
    def _convert_personality_type_string_to_enum(personality_type_str: str) -> PersonalityType:
        """
        성격 유형 문자열을 enum으로 변환
        
        Args:
            personality_type_str: 성격 유형 문자열
            
        Returns:
            PersonalityType: 성격 유형 enum
        """
        try:
            # 문자열과 enum 매핑
            for personality_type in PersonalityType:
                if personality_type.value == personality_type_str:
                    return personality_type
            
            # 매칭되지 않으면 기본값
            logger.warning(f"알 수 없는 성격 유형: {personality_type_str}, 기본값 사용")
            return PersonalityType.GENTLE
        except Exception as e:
            logger.warning(f"성격 유형 변환 오류: {e}, 기본값 사용")
            return PersonalityType.GENTLE
    
    @staticmethod
    def _convert_days_off_to_string(days_off: Optional[List]) -> str:
        """
        휴무일 목록을 문자열로 변환
        
        Args:
            days_off: 휴무일 목록 (DayOfWeek enum 또는 문자열)
            
        Returns:
            str: 휴무일 문자열 (콤마로 구분)
        """
        try:
            if not days_off:
                return ""
            
            # enum을 한국어로 변환
            day_mapping = {
                "MONDAY": "월", "TUESDAY": "화", "WEDNESDAY": "수", 
                "THURSDAY": "목", "FRIDAY": "금", "SATURDAY": "토", "SUNDAY": "일"
            }
            
            korean_days = []
            for day in days_off:
                if isinstance(day, str):
                    korean_day = day_mapping.get(day.upper(), day)
                    korean_days.append(korean_day)
                elif hasattr(day, 'value'):
                    korean_day = day_mapping.get(day.value, day.value)
                    korean_days.append(korean_day)
            
            return ",".join(korean_days)
            
        except Exception as e:
            logger.warning(f"휴무일 변환 오류: {e}")
            return ""
    
    @staticmethod
    def _get_primary_service_type(service_types: Optional[List]) -> ServiceType:
        """
        서비스 유형 목록에서 첫 번째 유형 반환
        
        Args:
            service_types: 서비스 유형 목록
            
        Returns:
            ServiceType: 주요 서비스 유형
        """
        try:
            if not service_types:
                return ServiceType.VISITING_CARE
            
            first_service = service_types[0]
            return ModelConverter._convert_service_type_string_to_enum(first_service)
            
        except Exception as e:
            logger.warning(f"주요 서비스 유형 추출 오류: {e}")
            return ServiceType.VISITING_CARE