from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
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
from ..entities.base import PersonalityType, ServiceType
from ..services.data_service import MatchingDataService
from ..services.model_converter import ModelConverter
from ..services.dependencies import get_matching_data_service

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/recommend", response_model=MatchingResponseDTO)
async def recommend_matching(
    request: MatchingRequestDTO,
    data_service: MatchingDataService = Depends(get_matching_data_service)
):
    """
    매칭 처리 API - DTO 정보 직접 활용 + 요양보호사만 ORM 조회
    
    1. DTO 정보로 직접 ConsumerForMatching 생성
    2. 서비스 타입으로 요양보호사 목록만 ORM 조회  
    3. 매칭 알고리즘 실행하여 최고 점수 1명 선택
    4. 선택된 요양보호사 정보를 MatchingResponseDTO로 반환
    """
    try:
        logger.info(f"매칭 요청 받음 - 서비스 요청 ID: {request.serviceRequestId}")
        
        # 1. DTO 정보로 직접 ConsumerForMatching 생성
        consumer_matching = create_consumer_from_dto(request)
        if not consumer_matching:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="수요자 데이터 변환에 실패했습니다"
            )
        
        logger.info(f"수요자 정보 생성 완료 - 서비스 타입: {consumer_matching.service_type.value}")
        
        # 2. 요양보호사 목록 조회 (서비스 타입 기준) - 주입받은 서비스 사용  
        caregivers = await data_service.get_available_caregivers(request)
        if not caregivers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조건에 맞는 요양보호사가 없습니다"
            )
        
        # 3. 요양보호사 Entity를 Matching 모델로 변환
        caregivers_matching = ModelConverter.caregivers_to_matching_models(caregivers)
        if not caregivers_matching:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="요양보호사 데이터 변환에 실패했습니다"
            )
        
        logger.info(f"데이터 변환 완료 - 수요자: 1명, 요양보호사: {len(caregivers_matching)}명")
        
        # 4. 매칭 알고리즘 실행
        matched_caregivers = await execute_matching_algorithm(consumer_matching, caregivers_matching)
        
        if not matched_caregivers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="매칭 조건을 만족하는 요양보호사가 없습니다"
            )
        
        # 5. 최고 점수 요양보호사 1명 선택
        best_match = matched_caregivers[0]  # 이미 점수 순으로 정렬됨
        
        # 6. 원본 요양보호사 데이터 찾기
        best_caregiver = next(
            (c for c in caregivers if c.caregiver_id == best_match.caregiver_id),
            None
        )
        
        if not best_caregiver:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="매칭된 요양보호사 정보를 찾을 수 없습니다"
            )
        
        # 7. 현재 DTO 구조에 맞는 응답 생성
        response = MatchingResponseDTO(
            caregiverId=best_caregiver.caregiver_id,
            availableStartTime=best_caregiver.available_start_time,
            availableEndTime=best_caregiver.available_end_time,
            address=best_caregiver.address,
            location=best_caregiver.location
        )
        
        logger.info(f"매칭 완료 - 선택된 요양보호사: {best_caregiver.caregiver_id} (점수: {best_match.match_score})")
        return response
        
    except HTTPException:
        raise  # HTTP 예외는 그대로 전달
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

def create_consumer_from_dto(request: MatchingRequestDTO) -> ConsumerForMatching:
    """
    MatchingRequestDTO를 ConsumerForMatching으로 변환
    
    Args:
        request: 매칭 요청 DTO
        
    Returns:
        ConsumerForMatching: 매칭용 수요자 모델
    """
    try:
        # 1. 서비스 유형 변환 (문자열 → Enum)
        service_type = None
        for st in ServiceType:
            if st.value == request.serviceType:
                service_type = st
                break
        
        if not service_type:
            logger.warning(f"알 수 없는 서비스 유형: {request.serviceType}, 기본값 사용")
            service_type = ServiceType.VISITING_CARE
        
        # 2. 요청 요일 변환 (숫자 리스트 → 문자열)
        day_mapping = {1: "월", 2: "화", 3: "수", 4: "목", 5: "금", 6: "토", 7: "일"}
        requested_days_str = ",".join([
            day_mapping.get(day, str(day)) for day in request.requestedDays
        ])
        
        # 3. 선호 시간 변환
        if request.preferred_time_start and request.preferred_time_end:
            start_time = request.preferred_time_start.strftime("%H:%M")
            end_time = request.preferred_time_end.strftime("%H:%M")
            preferred_time = TimeRange(start=start_time, end=end_time)
        else:
            # 기본 시간 설정
            preferred_time = TimeRange(start="09:00", end="18:00")
        
        # 4. 성격 유형 (기본값 사용 - 추후 DTO에 추가 시 확장 가능)
        personality_type = PersonalityType.GENTLE  # 기본값
        
        # 5. ConsumerForMatching 생성
        consumer = ConsumerForMatching(
            service_type=service_type,
            requested_days=requested_days_str,
            preferred_time=preferred_time,
            address=request.address,
            location=request.location,
            personality_type=personality_type
        )
        
        logger.info(f"DTO → Consumer 변환 완료: {service_type.value}, 요일: {requested_days_str}")
        return consumer
        
    except Exception as e:
        logger.error(f"DTO → Consumer 변환 오류: {e}")
        return None

def generate_match_reason(
    consumer: ConsumerForMatching, 
    caregiver: CaregiverForMatching, 
    score: float, 
    distance_value: float,
    rank: int
) -> str:
    """
    매칭 이유 생성
    
    Args:
        consumer: 수요자 정보
        caregiver: 요양보호사 정보
        score: 매칭 점수
        distance_value: 거리 값 (km)
        rank: 순위
    
    Returns:
        str: 매칭 이유 설명
    """
    try:
        reasons = []
        
        # 순위 정보
        rank_desc = f"{rank}순위"
        reasons.append(rank_desc)
        
        # 거리 정보
        if distance_value < 5.0:
            distance_desc = f"매우 가까운 거리 ({distance_value}km)"
        elif distance_value < 10.0:
            distance_desc = f"가까운 거리 ({distance_value}km)"
        elif distance_value < 20.0:
            distance_desc = f"적절한 거리 ({distance_value}km)"
        else:
            distance_desc = f"거리 {distance_value}km"
        reasons.append(distance_desc)
        
        # 서비스 유형 일치
        if consumer.service_type == caregiver.service_type:
            reasons.append(f"서비스 유형 일치 ({consumer.service_type.value})")
        
        # 시간대 호환성
        consumer_time_desc = f"{consumer.preferred_time.start}-{consumer.preferred_time.end}"
        caregiver_time_desc = f"{caregiver.available_times.start}-{caregiver.available_times.end}"
        reasons.append(f"시간대 호환 (요청: {consumer_time_desc}, 가능: {caregiver_time_desc})")
        
        # 요일 호환성
        if consumer.requested_days and caregiver.closed_days:
            reasons.append("요일 호환성 확인")
        
        # 경력 정보 (있는 경우)
        if caregiver.career_years > 0:
            if caregiver.career_years >= 5:
                reasons.append(f"풍부한 경력 ({caregiver.career_years}년)")
            elif caregiver.career_years >= 3:
                reasons.append(f"충분한 경력 ({caregiver.career_years}년)")
            else:
                reasons.append(f"경력 {caregiver.career_years}년")
        
        # 최종 점수
        reasons.append(f"매칭 점수 {score}점")
        
        return " | ".join(reasons)
        
    except Exception as e:
        logger.warning(f"매칭 이유 생성 오류: {e}")
        return f"{rank}순위 | 거리 {distance_value}km | 점수 {score}점"