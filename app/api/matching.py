from fastapi import APIRouter, HTTPException, status
from typing import List
import logging
import math

# 스키마 import
from ..dto.matching import MatchingRequestDTO, MatchingResponseDTO, MatchedCaregiverDTO, CaregiverForMatchingDTO
from ..models.matching import MatchedCaregiver, CaregiverForMatching

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/recommend", response_model=MatchingResponseDTO)
async def recommend_matching(request: MatchingRequestDTO):
    """
    거리 기반 매칭 처리 API
    
    1. 서비스 요청 위치와 요양보호사 후보군을 DTO로 받음
    2. Haversine 공식으로 거리 계산
    3. 거리 순으로 정렬하여 최대 5명 반환
    """
    try:
        logger.info(f"매칭 요청 받음 - 서비스 요청 ID: {request.serviceRequest.serviceRequestId}")
        
        # 1. 요양보호사 후보군 검증
        if not request.candidateCaregivers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="요양보호사 후보군이 제공되지 않았습니다"
            )
        
        # 2. DTO를 매칭 모델로 변환
        caregivers_matching = convert_dto_caregivers_to_matching_models(request.candidateCaregivers)
        if not caregivers_matching:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="요양보호사 데이터 변환에 실패했습니다"
            )
        
        logger.info(f"매칭 대상 요양보호사: {len(caregivers_matching)}명")
        
        # 3. 거리 기반 매칭 알고리즘 실행
        service_location = request.serviceRequest.location.get_coordinates()
        matched_caregivers = execute_distance_matching(service_location, caregivers_matching)
        
        if not matched_caregivers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="매칭할 수 있는 요양보호사가 없습니다"
            )
        
        # 4. 최대 5명까지 선택
        top_matches = matched_caregivers[:5]
        
        # 5. 매칭된 요양보호사 DTO 리스트 생성
        matched_caregiver_dtos = []
        for match in top_matches:
            # 원본 요양보호사 DTO 데이터 찾기
            caregiver_dto = next(
                (c for c in request.candidateCaregivers if c.caregiverId == match.caregiver_id),
                None
            )
            
            if caregiver_dto:
                matched_dto = MatchedCaregiverDTO(
                    caregiverId=caregiver_dto.caregiverId,
                    availableTimes=caregiver_dto.availableTimes,
                    address=caregiver_dto.address,
                    location=caregiver_dto.baseLocation,
                    matchScore=match.match_score,
                    matchReason=match.reason,
                    distanceKm=getattr(match, 'distance_km', None),
                    estimatedTravelTime=getattr(match, 'estimated_travel_time', None),
                    career=caregiver_dto.career,
                    serviceType=caregiver_dto.serviceType,
                    isVerified=caregiver_dto.isVerified
                )
                matched_caregiver_dtos.append(matched_dto)
        
        if not matched_caregiver_dtos:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="매칭된 요양보호사 정보를 찾을 수 없습니다"
            )
        
        # 6. 응답 생성
        response = MatchingResponseDTO(
            matchedCaregivers=matched_caregiver_dtos,
            totalMatches=len(matched_caregiver_dtos)
        )
        
        logger.info(f"매칭 완료 - 선택된 요양보호사: {len(matched_caregiver_dtos)}명")
        return response
        
    except HTTPException:
        raise  # HTTP 예외는 그대로 전달
    except Exception as e:
        logger.error(f"매칭 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매칭 처리 중 오류가 발생했습니다: {str(e)}"
        )

def execute_distance_matching(service_location: List[float], caregivers: List[CaregiverForMatching]) -> List[MatchedCaregiver]:
    """
    거리 기반 매칭 알고리즘
    
    Args:
        service_location: 서비스 요청 위치 [위도, 경도]
        caregivers: 요양보호사 리스트
    
    Returns:
        List[MatchedCaregiver]: 거리 순으로 정렬된 매칭 결과
    """
    
    if not caregivers:
        logger.info("매칭할 요양보호사가 없습니다")
        return []
    
    caregiver_distances = []
    
    # 모든 요양보호사에 대해 거리 계산
    for caregiver in caregivers:
        caregiver_location = caregiver.base_location.get_coordinates()
        distance_km = calculate_haversine_distance(service_location, caregiver_location)
        caregiver_distances.append({
            'caregiver': caregiver,
            'distance_km': distance_km
        })
    
    # 거리 순으로 정렬 (가까운 순서)
    caregiver_distances.sort(key=lambda x: x['distance_km'])
    
    # 거리 기반 점수 부여 (상위 5명까지 10, 8, 6, 4, 2점)
    score_mapping = [10, 8, 6, 4, 2]
    matched_caregivers = []
    
    for i, item in enumerate(caregiver_distances):
        if i < len(score_mapping):
            score = score_mapping[i]
        else:
            score = 1  # 6위 이하는 1점
        
        caregiver = item['caregiver']
        distance_km = item['distance_km']
        
        matched_caregiver = MatchedCaregiver(
            caregiver_id=caregiver.caregiver_id,
            match_score=float(score),
            reason=generate_distance_match_reason(distance_km, score, i + 1, caregiver.career_years)
        )
        matched_caregivers.append(matched_caregiver)
    
    logger.info(f"거리 기반 매칭 완료: {len(matched_caregivers)}명")
    for i, match in enumerate(matched_caregivers[:5], 1):
        distance = caregiver_distances[i-1]['distance_km']
        logger.info(f"{i}순위: {match.caregiver_id} (거리: {distance:.2f}km, 점수: {match.match_score})")
    
    return matched_caregivers

def calculate_haversine_distance(location1: List[float], location2: List[float]) -> float:
    """
    Haversine 공식을 사용하여 두 GPS 좌표 간의 거리를 계산
    
    Args:
        location1: 첫 번째 지점의 [위도, 경도]
        location2: 두 번째 지점의 [위도, 경도]
    
    Returns:
        두 지점 간의 거리 (km)
    """
    try:
        if not location1 or not location2 or len(location1) != 2 or len(location2) != 2:
            logger.warning("잘못된 좌표 형식")
            return 999.0  # 매우 큰 거리 값
        
        lat1, lon1 = location1
        lat2, lon2 = location2
        
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
        
        return round(distance, 2)
            
    except Exception as e:
        logger.warning(f"거리 계산 오류: {e}")
        return 999.0

def convert_dto_caregivers_to_matching_models(caregiver_dtos: List[CaregiverForMatchingDTO]) -> List[CaregiverForMatching]:
    """
    CaregiverForMatchingDTO 목록을 CaregiverForMatching 목록으로 변환
    
    Args:
        caregiver_dtos: DTO 요양보호사 목록
        
    Returns:
        List[CaregiverForMatching]: 매칭용 요양보호사 모델 목록
    """
    try:
        matching_caregivers = []
        
        for dto in caregiver_dtos:
            caregiver_matching = CaregiverForMatching(
                caregiver_id=dto.caregiverId,
                base_location=dto.baseLocation,
                career_years=dto.careerYears,
                available_times=dto.availableTimes,
                service_type=dto.serviceType,
                days_off=dto.daysOff,
                work_area=dto.workArea
            )
            matching_caregivers.append(caregiver_matching)
        
        logger.info(f"DTO → Matching 모델 변환 완료: {len(matching_caregivers)}명")
        return matching_caregivers
        
    except Exception as e:
        logger.error(f"DTO → Matching 모델 변환 오류: {e}")
        return []

def generate_distance_match_reason(distance_km: float, score: float, rank: int, career_years: int) -> str:
    """
    거리 기반 매칭 이유 생성
    
    Args:
        distance_km: 거리 (km)
        score: 매칭 점수
        rank: 순위
        career_years: 경력 년수
    
    Returns:
        str: 매칭 이유 설명
    """
    try:
        reasons = []
        
        # 순위 정보
        reasons.append(f"{rank}순위")
        
        # 거리 정보
        if distance_km < 5.0:
            distance_desc = f"매우 가까운 거리 ({distance_km}km)"
        elif distance_km < 10.0:
            distance_desc = f"가까운 거리 ({distance_km}km)"
        elif distance_km < 20.0:
            distance_desc = f"적절한 거리 ({distance_km}km)"
        else:
            distance_desc = f"거리 {distance_km}km"
        reasons.append(distance_desc)
        
        # 경력 정보 (있는 경우)
        if career_years > 0:
            if career_years >= 5:
                reasons.append(f"풍부한 경력 ({career_years}년)")
            elif career_years >= 3:
                reasons.append(f"충분한 경력 ({career_years}년)")
            else:
                reasons.append(f"경력 {career_years}년")
        
        # 최종 점수
        reasons.append(f"매칭 점수 {score}점")
        
        return " | ".join(reasons)
        
    except Exception as e:
        logger.warning(f"매칭 이유 생성 오류: {e}")
        return f"{rank}순위 | 거리 {distance_km}km | 점수 {score}점"