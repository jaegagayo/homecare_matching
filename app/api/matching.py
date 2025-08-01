from fastapi import APIRouter, HTTPException, status
from typing import List
import logging

# 스키마 import
from ..dto.matching import MatchingRequestDTO, MatchingResponseDTO
from ..models.matching import (
    MatchedCaregiver,
    ConsumerForMatching, 
    CaregiverForMatching,
    TimeRange
)
from ..entities.base import PersonalityType

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/recommend", response_model=MatchingResponseDTO)
async def recommend_matching(request: MatchingRequestDTO):
    """
    매칭 처리 API
    Spring 서버에서 수요자와 요양보호사 정보를 받아 매칭 처리 후 결과 반환
    """
    try:
        logger.info(f"매칭 요청 받음 - 수요자: {request.consumer.serviceRequest_id}, 요양보호사 수: {len(request.caregivers)}")
        
        # 매칭 알고리즘 실행
        matched_caregivers = await execute_matching_algorithm(request.consumer, request.caregivers)
        
        # 매칭 점수 기준으로 정렬 (높은 점수 순)
        matched_caregivers.sort(key=lambda x: x.match_score or 0, reverse=True)
        
        # 응답 생성
        response = MatchingResponseDTO(
            matched_caregivers=matched_caregivers,
            total_matches=len(matched_caregivers),
            status="success",
            message=f"{len(matched_caregivers)}명의 요양보호사가 매칭되었습니다."
        )
        
        logger.info(f"매칭 완료 - 총 {len(matched_caregivers)}명 매칭")
        return response
        
    except Exception as e:
        logger.error(f"매칭 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매칭 처리 중 오류가 발생했습니다: {str(e)}"
        )

async def execute_matching_algorithm(
    consumer: ConsumerForMatching, 
    caregivers: List[CaregiverForMatching]
) -> List[MatchedCaregiver]:
    """
    고도화된 매칭 알고리즘 실행
    
    1단계: 필터링 (필수 조건)
    - 서비스 유형 일치
    - 요일 호환성 (휴무일 vs 요청일)
    - 시간대 호환성 (근무시간 vs 선호시간)
    
    2단계: 점수 선호도 계산
    - 거리 매칭 (가중치 1.0)
    - 성격 매칭 (가중치 0)
    """
    matched_caregivers = []
    
    for caregiver in caregivers:
        # 1단계: 필터링 검사
        if not pass_filtering_criteria(consumer, caregiver):
            continue  # 필터링 통과 못하면 제외
        
        # 2단계: 점수 계산
        preference_score = calculate_preference_score(consumer, caregiver)
        
        matched_caregiver = MatchedCaregiver(
            caregiver_id=caregiver.caregiver_id,
            match_score=round(preference_score, 2),
            reason=generate_match_reason(consumer, caregiver, preference_score)
        )
        matched_caregivers.append(matched_caregiver)
    
    logger.info(f"필터링 통과: {len(matched_caregivers)}명")
    return matched_caregivers

def pass_filtering_criteria(consumer: ConsumerForMatching, caregiver: CaregiverForMatching) -> bool:
    """
    필터링 기준 검사 (필수 조건)
    모든 조건을 만족해야 True 반환
    """
    
    # 1. 서비스 유형 일치 검사
    if not check_service_type_match(consumer.service_type, caregiver.service_type):
        logger.debug(f"서비스 유형 불일치: {consumer.service_type} != {caregiver.service_type}")
        return False
    
    # 2. 요일 호환성 검사 (요청일에 휴무가 아닌지)
    if not check_day_availability(consumer.requested_days, caregiver.closed_days):
        logger.debug(f"요일 호환성 실패: 요청일({consumer.requested_days}) vs 휴무일({caregiver.closed_days})")
        return False
    
    # 3. 시간대 호환성 검사 (선호시간과 근무시간 겹침)
    if not check_time_availability(consumer.preferred_time, caregiver.available_times):
        logger.debug(f"시간대 호환성 실패: {consumer.preferred_time} vs {caregiver.available_times}")
        return False
    
    return True

def check_service_type_match(consumer_service: str, caregiver_service: str) -> bool:
    """서비스 유형 일치 검사"""
    return consumer_service == caregiver_service

def check_day_availability(requested_days: str, closed_days: str) -> bool:
    """요일 호환성 검사 - 요청일에 휴무가 아닌지 확인"""
    try:
        if not requested_days or not closed_days:
            return True  # 데이터가 없으면 통과
        
        requested_set = set(day.strip() for day in requested_days.split(',') if day.strip())
        closed_set = set(day.strip() for day in closed_days.split(',') if day.strip())
        
        # 요청일과 휴무일이 겹치면 안됨
        conflict_days = requested_set.intersection(closed_set)
        return len(conflict_days) == 0
        
    except Exception as e:
        logger.warning(f"요일 호환성 검사 오류: {e}")
        return False

def check_time_availability(consumer_time, caregiver_time) -> bool:
    """시간대 호환성 검사 - 선호시간과 근무시간이 겹치는지 확인"""
    try:
        consumer_start = consumer_time.start
        consumer_end = consumer_time.end
        caregiver_start = caregiver_time.start
        caregiver_end = caregiver_time.end
        
        # 시간 문자열을 분으로 변환하여 비교
        consumer_start_min = time_to_minutes(consumer_start)
        consumer_end_min = time_to_minutes(consumer_end)
        caregiver_start_min = time_to_minutes(caregiver_start)
        caregiver_end_min = time_to_minutes(caregiver_end)
        
        # 시간대가 겹치는지 확인
        return not (consumer_end_min <= caregiver_start_min or consumer_start_min >= caregiver_end_min)
        
    except Exception as e:
        logger.warning(f"시간 호환성 검사 오류: {e}")
        return False

def time_to_minutes(time_str: str) -> int:
    """시간 문자열을 분으로 변환 (예: "09:30" -> 570)"""
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except:
        return 0

def calculate_preference_score(consumer: ConsumerForMatching, caregiver: CaregiverForMatching) -> float:
    """
    점수 선호도 계산
    - 거리 매칭: 가중치 0.6
    - 성격 매칭: 가중치 0.4
    총점: 10점 만점
    """
    
    # 1. 거리 점수 계산 (0-10점)
    distance_score = calculate_distance_score(consumer.location, caregiver.base_location)
    
    # 2. 성격 점수 계산 (0-10점)
    personality_score = calculate_personality_score(consumer.personality_type, caregiver.personality_type)
    
    # 3. 가중치 적용하여 총점 계산
    total_score = (distance_score * 0.6) + (personality_score * 0.4)
    
    return min(total_score, 10.0)

def calculate_distance_score(consumer_location: str, caregiver_location: str) -> float:
    """
    거리 점수 계산 (0-10점)
    점수 단계: 10, 8, 6, 4, 2, 0
    """
    try:
        # 간단한 문자열 기반 유사도 계산
        consumer_parts = set(consumer_location.replace(',', ' ').split())
        caregiver_parts = set(caregiver_location.replace(',', ' ').split())
        
        if not consumer_parts or not caregiver_parts:
            return 2.0  # 기본값
        
        # 공통 키워드 비율 계산
        common_parts = consumer_parts.intersection(caregiver_parts)
        total_parts = consumer_parts.union(caregiver_parts)
        similarity_ratio = len(common_parts) / len(total_parts) if total_parts else 0
        
        # 유사도에 따른 점수 매핑 (6단계)
        if similarity_ratio >= 0.8:
            return 10.0  # 매우 가까움
        elif similarity_ratio >= 0.6:
            return 8.0   # 가까움
        elif similarity_ratio >= 0.4:
            return 6.0   # 보통
        elif similarity_ratio >= 0.2:
            return 4.0   # 약간 멀음
        elif similarity_ratio > 0:
            return 2.0   # 멀음
        else:
            return 0.0   # 매우 멀음
            
    except Exception as e:
        logger.warning(f"거리 점수 계산 오류: {e}")
        return 2.0

def calculate_personality_score(consumer_personality: PersonalityType, caregiver_personality: PersonalityType) -> float:
    """
    성격 점수 계산 (0-10점)
    점수 단계: 10, 8, 6, 4, 2, 0
    """
    # 성격 호환성 매트릭스 (6단계 점수)
    compatibility_matrix = {
        PersonalityType.GENTLE: {
            PersonalityType.GENTLE: 10.0,   # 완벽 매칭
            PersonalityType.CALM: 8.0,      # 우수 매칭
            PersonalityType.CHEERFUL: 6.0,  # 좋은 매칭
            PersonalityType.ACTIVE: 4.0     # 보통 매칭
        },
        PersonalityType.ACTIVE: {
            PersonalityType.ACTIVE: 10.0,
            PersonalityType.CHEERFUL: 8.0,
            PersonalityType.GENTLE: 4.0,
            PersonalityType.CALM: 2.0       # 어려운 매칭
        },
        PersonalityType.CALM: {
            PersonalityType.CALM: 10.0,
            PersonalityType.GENTLE: 8.0,
            PersonalityType.CHEERFUL: 6.0,
            PersonalityType.ACTIVE: 2.0
        },
        PersonalityType.CHEERFUL: {
            PersonalityType.CHEERFUL: 10.0,
            PersonalityType.ACTIVE: 8.0,
            PersonalityType.GENTLE: 6.0,
            PersonalityType.CALM: 6.0
        }
    }
    
    return compatibility_matrix.get(consumer_personality, {}).get(caregiver_personality, 4.0)

def generate_match_reason(consumer: ConsumerForMatching, caregiver: CaregiverForMatching, score: float) -> str:
    """매칭 이유 생성"""
    reasons = []
    
    # 서비스 유형 (필터링 통과했으므로 항상 일치)
    reasons.append(f"서비스 유형 일치({consumer.service_type.value})")
    
    # 거리 점수 분석
    distance_score = calculate_distance_score(consumer.location, caregiver.base_location)
    if distance_score >= 8:
        reasons.append("지역 매우 근접")
    elif distance_score >= 6:
        reasons.append("지역 근접")
    elif distance_score >= 4:
        reasons.append("지역 접근성 양호")
    
    # 성격 점수 분석
    personality_score = calculate_personality_score(consumer.personality_type, caregiver.personality_type)
    if personality_score >= 8:
        reasons.append("성격 매칭 우수")
    elif personality_score >= 6:
        reasons.append("성격 매칭 양호")
    
    # 경력 정보 추가
    if caregiver.career_years >= 5:
        reasons.append("풍부한 경력")
    elif caregiver.career_years >= 2:
        reasons.append("적절한 경력")
    
    return ", ".join(reasons) if reasons else f"매칭 점수 {score:.1f}점"