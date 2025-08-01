from fastapi import APIRouter, HTTPException, status
from typing import List
import logging
import math

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
        
        # 응답 생성
        if matched_caregivers:
            message = f"최적의 요양보호사 1명이 매칭되었습니다."
        else:
            message = "조건에 맞는 요양보호사가 없습니다."
            
        response = MatchingResponseDTO(
            matched_caregivers=matched_caregivers,
            total_matches=len(matched_caregivers),
            status="success",
            message=message
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
    매칭 알고리즘
    
    1단계: 필터링 (필수 조건)
    - 서비스 유형 일치
    - 요일 호환성 (휴무일 vs 요청일)
    - 시간대 호환성 (근무시간 vs 선호시간)
    
    2단계: 점수 선호도 계산
    - 거리 매칭 (가중치 1.0)
    - 성격 매칭 (가중치 0) *MVP에서 미구현*
    - 경력 매칭 (가중치 0) *MVP에서 미구현*
    
    결과: 가장 높은 점수를 획득한 1명의 요양보호사 반환
    """
    # 1단계: 필터링
    filtered_caregivers = []
    for caregiver in caregivers:
        if pass_filtering_criteria(consumer, caregiver):
            filtered_caregivers.append(caregiver)
    
    logger.info(f"필터링 통과: {len(filtered_caregivers)}명")
    
    if not filtered_caregivers:
        return []  # 필터링 통과한 요양보호사가 없음
    
    # 2단계: 거리 기반 점수 계산 및 정렬
    matched_caregivers = calculate_distance_based_scores(consumer, filtered_caregivers)
    
    # 가장 높은 점수 1명만 반환
    if matched_caregivers:
        best_match = matched_caregivers[0]  # 이미 점수 순으로 정렬됨
        logger.info(f"최종 매칭: {best_match.caregiver_id} (점수: {best_match.match_score})")
        return [best_match]
    
    return []

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

def calculate_distance_based_scores(consumer: ConsumerForMatching, caregivers: List[CaregiverForMatching]) -> List[MatchedCaregiver]:
    """
    거리 기반 점수 계산 및 매칭
    - 거리 값 계산 후 정렬
    - 상위 5명까지 점수 부여 (10, 8, 6, 4, 2)
    - 점수 순으로 정렬하여 반환
    """
    caregiver_distances = []
    
    # 모든 요양보호사에 대해 거리 값 계산
    for caregiver in caregivers:
        distance_value = calculate_distance_value(consumer.location, caregiver.base_location)
        caregiver_distances.append({
            'caregiver': caregiver,
            'distance_value': distance_value
        })
    
    # 거리 값으로 정렬 (거리가 가까운 순서대로)
    caregiver_distances.sort(key=lambda x: x['distance_value'])
    
    # 상위 5명까지 점수 부여
    score_mapping = [10, 8, 6, 4, 2]  # 1위~5위 점수
    matched_caregivers = []
    
    for i, item in enumerate(caregiver_distances):
        if i < len(score_mapping):
            score = score_mapping[i]
        else:
            score = 0  # 6위 이하는 0점
        
        caregiver = item['caregiver']
        matched_caregiver = MatchedCaregiver(
            caregiver_id=caregiver.caregiver_id,
            match_score=float(score),
            reason=generate_match_reason(consumer, caregiver, score, item['distance_value'], i + 1)
        )
        matched_caregivers.append(matched_caregiver)
    
    # 점수 순으로 정렬 (높은 점수 순)
    matched_caregivers.sort(key=lambda x: x.match_score, reverse=True)
    
    return matched_caregivers

def calculate_distance_value(consumer_location: List[float], caregiver_location: List[float]) -> float:
    """
    GPS 좌표 기반 거리 계산 (Haversine 공식)
    
    Args:
        consumer_location: 수요자 위치 [위도, 경도]
        caregiver_location: 요양보호사 위치 [위도, 경도]
    
    Returns:
        두 지점 간의 거리 (km)
    """
    try:
        if not consumer_location or not caregiver_location or len(consumer_location) != 2 or len(caregiver_location) != 2:
            logger.warning("잘못된 좌표 형식")
            return 999.0  # 매우 큰 거리 값
        
        lat1, lon1 = consumer_location
        lat2, lon2 = caregiver_location
        
        # Haversine 공식을 사용한 두 GPS 좌표 간 거리 계산
        distance_km = haversine_distance(lat1, lon1, lat2, lon2)
        
        return round(distance_km, 2)
            
    except Exception as e:
        logger.warning(f"거리 값 계산 오류: {e}")
        return 999.0

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine 공식을 사용하여 두 GPS 좌표 간의 거리를 계산
    
    Args:
        lat1, lon1: 첫 번째 지점의 위도, 경도
        lat2, lon2: 두 번째 지점의 위도, 경도
    
    Returns:
        두 지점 간의 거리 (km)
    """
    # 지구의 반지름 (km)
    R = 6371.0
    
    # 위도, 경도를 라디안으로 변환
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 위도, 경도 차이 계산
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine 공식
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 거리 계산
    distance = R * c
    
    return distance