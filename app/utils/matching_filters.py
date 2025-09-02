"""
요양보호사 매칭 필터링 유틸리티 모듈

CaregiverPreference DTO 기반의 다양한 필터링 로직을 제공합니다.
주로 LLM이 변환한 구조화된 선호조건과 서비스 요청을 매칭하는데 사용됩니다.
"""

import logging

from ..dto.matching import MatchingRequestDTO
from ..dto.matching import CaregiverForMatchingDTO

logger = logging.getLogger(__name__)

async def evaluate_caregiver_match(
    caregiver: CaregiverForMatchingDTO, 
    request: MatchingRequestDTO
) -> bool:
    """요양보호사의 선호조건과 서비스 요청을 매칭하여 적합성 평가 (True/False 필터)"""
    try:
        # LLM이 변환한 선호조건이 None이거나 필드들이 null인 경우 기본적으로 통과
        # if structured_preferences is None:
        #     logger.debug(f"요양보호사 {caregiver.caregiver_id}: 선호조건 없음 - 기본 통과")
        #     return True
        
        # 필터링 로직 구현
        # 모든 조건을 만족해야 True 반환
    
        if not filter_by_service_type(caregiver, request):
            logger.debug(f"요양보호사 {caregiver.caregiver_id} 서비스 유형 불일치")
            return False
        
        if not filter_by_supported_conditions(caregiver, request):
            logger.debug(f"요양보호사 {caregiver.caregiver_id} 지원 질환 불일치")
            return False
        
        # # 4. 선호 연령/성별 필터링
        # if not filter_by_preferred_demographics(structured_preferences, request):
        #     logger.debug(f"요양보호사 {caregiver.caregiver_id} 선호 연령/성별 불일치")
        #     return False
        
        # # 5. 요일 필터링
        # if not filter_by_day_of_week(structured_preferences, request):
        #     logger.debug(f"요양보호사 {caregiver.caregiver_id} 요일 불일치")
        #     return False
        
        # 모든 필터 통과 시 적합하다고 판단
        return True
        
    except Exception as e:
        logger.warning(f"매칭 평가 중 오류: {str(e)}")
        # 오류 발생 시 기본적으로 적합하지 않다고 판단 (안전한 필터링)
        return False

def filter_by_service_type(caregiver: CaregiverForMatchingDTO, request: MatchingRequestDTO) -> bool:
    """서비스 유형 필터링: 요양보호사의 선호 서비스 유형과 요청 서비스 유형 매칭"""
    # 선호조건 또는 요청에 serviceType가 없거나 비어있으면 기본 통과
    if not hasattr(caregiver, 'serviceType') or not caregiver.serviceType:
        return True
    if not request.serviceRequest.serviceType:
        return True
    
    # 요청 서비스 유형이 요양보호사의 선호 서비스 유형 목록에 있는지 확인
    return request.serviceRequest.serviceType in caregiver.serviceType

def filter_by_supported_conditions(caregiver: CaregiverForMatchingDTO, request: MatchingRequestDTO) -> bool:
    """지원 질환 필터링: 요양보호사의 지원 질환과 요청 추가 정보 매칭"""
    # 선호조건 또는 요청에 supported_conditions가 없거나 비어있으면 기본 통과
    if not hasattr(caregiver, 'supportedCondition') or not caregiver.supportedCondition:
        return True
    if not request.serviceRequest.additionalInformation:
        return True
    
    # TODO 간단한 키워드 매칭으로 구현 (실제로는 더 정교한 NLP 처리 필요)
    additional_info = request.serviceRequest.additionalInformation.lower()
    for condition in caregiver.supportedCondition:
        if condition.lower() in additional_info:
            return True
    
    return False

# def filter_by_preferred_demographics(structured_preferences: Any, request: MatchingRequestDTO) -> bool:
#     """선호 연령/성별 필터링: 요양보호사의 선호 연령/성별과 요청 정보 매칭"""
#     # 선호조건에 preferred_gender, preferred_min_age, preferred_max_age가 없으면 기본 통과
#     has_gender_preference = hasattr(structured_preferences, 'preferred_gender') and structured_preferences.preferred_gender
#     has_age_preference = (hasattr(structured_preferences, 'preferred_min_age') and structured_preferences.preferred_min_age and
#                          hasattr(structured_preferences, 'preferred_max_age') and structured_preferences.preferred_max_age)
    
#     if not has_gender_preference and not has_age_preference:
#         return True
    
#     # 요청에 환자 정보가 없으면 기본 통과 (실제로는 요청 DTO에 환자 정보가 있어야 함)
#     # 여기서는 추가 정보에서 간단히 추정하는 예시
#     additional_info = request.serviceRequest.additionalInformation or ""
#     additional_info = additional_info.lower()
    
#     # 성별 필터링 (간단한 키워드 매칭)
#     if has_gender_preference:
#         preferred_gender = structured_preferences.preferred_gender.lower()
#         if "남성" in preferred_gender and "여성" not in additional_info:
#             return True
#         if "여성" in preferred_gender and "남성" not in additional_info:
#             return True
#         # 성별이 명시되지 않았거나 불일치하면 필터링
#         if preferred_gender not in additional_info:
#             return False
    
#     # 연령 필터링 (간단한 구현)
#     if has_age_preference:
#         try:
#             min_age = int(structured_preferences.preferred_min_age)
#             max_age = int(structured_preferences.preferred_max_age)
#             # 추가 정보에서 연령 추정 (실제로는 정확한 데이터 필요)
#             if "노인" in additional_info or "어르신" in additional_info:
#                 estimated_age = 70  # 예시 값
#             elif "성인" in additional_info:
#                 estimated_age = 40  # 예시 값
#             else:
#                 estimated_age = 50  # 기본 값
            
#             if not (min_age <= estimated_age <= max_age):
#                 return False
#         except (ValueError, TypeError):
#             # 숫자 변환 실패 시 기본 통과
#             pass
    
#     return True

# def filter_by_day_of_week(structured_preferences: Any, request: MatchingRequestDTO) -> bool:
#     """요일 필터링: 요양보호사의 선호 요일과 요청 날짜 매칭"""
#     # 선호조건에 day_of_week가 없거나 비어있으면 기본 통과
#     if not hasattr(structured_preferences, 'day_of_week') or not structured_preferences.day_of_week:
#         return True
    
#     # 요청에 requestDate가 없으면 기본 통과
#     if not request.serviceRequest.requestDate:
#         return True
    
#     # 요청 날짜에서 요일 추출 (간단한 구현)
#     try:
#         from datetime import datetime
#         request_date = datetime.strptime(request.serviceRequest.requestDate, "%Y-%m-%d")
#         request_weekday = request_date.strftime("%A")  # Monday, Tuesday, etc.
        
#         # 한국어 요일 매핑 (간단한 예시)
#         weekday_map = {
#             "Monday": "월요일",
#             "Tuesday": "화요일",
#             "Wednesday": "수요일",
#             "Thursday": "목요일",
#             "Friday": "금요일",
#             "Saturday": "토요일",
#             "Sunday": "일요일"
#         }
        
#         korean_weekday = weekday_map.get(request_weekday, "")
#         if korean_weekday and korean_weekday in structured_preferences.day_of_week:
#             return True
#     except (ValueError, TypeError):
#         # 날짜 파싱 실패 시 기본 통과
#         pass
    
#     return False