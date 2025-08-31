"""
위치 기반 요양보호사 매칭 시스템 API

매칭 프로세스:
1. 수요자 신청 정보로 서비스 요청 위치 DTO 수신
2. 선호시간대 필터링: 신청자 선호시간대와 요양보호사 근무시간대 겹침 확인
3. 서비스 요청 위치 반경 15km 내 요양보호사를 근거리 후보군으로 메모리에 로드
4. 근거리 후보군 내 요양보호사의 요구조건 비정형 텍스트를 LLM으로 선호조건 변환 후 필터링하여 조건부합 후보군 생성
5. 조건부합 후보군 내 요양보호사를 대상으로 각 사용자의 위치 간 예상 소요 시간 계산
6. 계산된 ETA를 정렬하여 ETA 값이 작은 순서대로 5명을 선정하여 최종 후보로 반환
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Tuple, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

# 스키마 import
from ..dto.matching import MatchingRequestDTO, MatchingResponseDTO, MatchedCaregiverDTO, CaregiverForMatchingDTO
from ..models.matching import MatchedCaregiver, CaregiverForMatching, LocationInfo
from ..dto.converting import ConvertNonStructuredDataToStructuredDataRequest
from ..api.converting import convert_non_structured_data_to_structured_data
from ..utils.location_calculator import filter_caregivers_by_distance, calculate_distance_km, calculate_estimated_travel_time
from ..utils.naver_direction import ETACalculator
from ..utils.time_utils import filter_caregivers_by_time_preference

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# ETA Calculator 인스턴스 생성 (목 데이터 사용)
eta_calculator = ETACalculator(
    use_mock_data=True,
    mock_data_path="tests/mock_data/naver_map_api_dataset.json"
)

class MatchingProcessError(Exception):
    """매칭 프로세스 오류"""
    def __init__(self, step: str, message: str, details: Dict[str, Any] = None):
        self.step = step
        self.message = message
        self.details = details or {}
        super().__init__(f"{step}: {message}")

@router.post("/recommend", response_model=MatchingResponseDTO)
async def recommend_matching(request: MatchingRequestDTO):
    """
    위치 기반 요양보호사 매칭 처리 API
    """
    processing_results = {}
    
    try:
        logger.info(f"매칭 요청 시작 - 서비스 요청 ID: {request.serviceRequest.serviceRequestId}")
        start_time = datetime.now()
        
        # 1. 서비스 요청 위치 DTO 수신 검증
        service_location = await validate_service_request(request)
        processing_results["request_validation"] = {"status": "success", "location": f"({service_location.y}, {service_location.x})"}
        logger.info("요청 검증 완료")
        
        # 2. 선호시간대 필터링 (요청 검증 후, 반경 필터링 전)
        time_filtered_candidates = await filter_by_time_preferences(request.candidateCaregivers, request.serviceRequest)
        processing_results["time_preference_filtering"] = {"status": "success", "count": len(time_filtered_candidates)}
        logger.info(f"선호시간대 필터링 완료: {len(time_filtered_candidates)}명")
        
        if not time_filtered_candidates:
            raise MatchingProcessError("time_preference_filtering", "선호시간대에 맞는 요양보호사가 없습니다",
                                     {"preferred_start_time": request.serviceRequest.preferredStartTime,
                                      "preferred_end_time": request.serviceRequest.preferredEndTime})
        
        # 3. 반경 15km 내 요양보호사 근거리 후보군 로드
        nearby_candidates = await load_nearby_caregivers(service_location, time_filtered_candidates)
        processing_results["radius_filtering"] = {"status": "success", "count": len(nearby_candidates)}
        logger.info(f"반경 필터링 완료: {len(nearby_candidates)}명")
        
        if not nearby_candidates:
            raise MatchingProcessError("radius_filtering", "15km 반경 내 요양보호사가 없습니다",
                                     {"radius_km": 15, "request_location": f"({service_location.y}, {service_location.x})"})
        
        # 4. LLM 선호조건 변환 및 필터링으로 조건부합 후보군 생성
        qualified_candidates = await filter_by_preferences(nearby_candidates, request)
        processing_results["preference_filtering"] = {"status": "success", "count": len(qualified_candidates)}
        logger.info(f"선호조건 필터링 완료: {len(qualified_candidates)}명")
        
        if not qualified_candidates:
            raise MatchingProcessError("preference_filtering", "선호조건에 맞는 요양보호사가 없습니다",
                                     {"filtered_count": 0, "original_count": len(nearby_candidates)})
        
        # 5. 각 사용자 위치 간 예상 소요 시간 계산
        eta_calculated_candidates = await calculate_travel_times(qualified_candidates, service_location)
        processing_results["eta_calculation"] = {"status": "success", "count": len(eta_calculated_candidates)}
        logger.info(f"ETA 계산 완료: {len(eta_calculated_candidates)}명")
        
        if not eta_calculated_candidates:
            raise MatchingProcessError("eta_calculation", "ETA 계산에 실패했습니다",
                                     {"calculation_failed_count": len(qualified_candidates)})
        
        # 6. ETA 기준 정렬 후 최종 5명 선정
        final_matches = await select_final_candidates(eta_calculated_candidates)
        processing_results["final_selection"] = {"status": "success", "count": len(final_matches)}
        logger.info(f"최종 선정 완료: {len(final_matches)}명")
        
        if not final_matches:
            raise MatchingProcessError("final_selection", "최종 후보 선정에 실패했습니다",
                                     {"eta_calculated_count": len(eta_calculated_candidates)})
        
        # 응답 DTO 생성
        matched_caregiver_dtos = await create_response_dtos(final_matches, request.candidateCaregivers)
        
        response = MatchingResponseDTO(
            matchedCaregivers=matched_caregiver_dtos,
            totalMatches=len(matched_caregiver_dtos),
            processingResults=processing_results,
            processingTimeMs=int((datetime.now() - start_time).total_seconds() * 1000)
        )
        
        logger.info(f"매칭 완료 - 최종 선정: {len(matched_caregiver_dtos)}명, "
                   f"처리시간: {response.processingTimeMs}ms")
        return response
        
    except MatchingProcessError as e:
        processing_results[e.step] = {
            "status": "failed",
            "error": e.message,
            "details": e.details
        }
        logger.error(f"{e.step} 실패: {e.message}")
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": f"{e.step} failed",
                "message": e.message,
                "details": e.details,
                "processing_results": processing_results
            }
        )
    
    except Exception as e:
        logger.error(f"매칭 처리 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Unexpected error during matching",
                "message": str(e),
                "processing_results": processing_results
            }
        )

async def validate_service_request(request: MatchingRequestDTO) -> LocationInfo:
    """서비스 요청 위치 DTO 수신 검증"""
    try:
        if not request.serviceRequest:
            raise MatchingProcessError("request_validation", "서비스 요청 정보가 없습니다")
        
        if not request.serviceRequest.location:
            raise MatchingProcessError("request_validation", "서비스 요청 위치 정보가 없습니다")
        
        location = request.serviceRequest.location
        if not isinstance(location.x, (int, float)) or not isinstance(location.y, (int, float)):
            raise MatchingProcessError("request_validation", "위치 좌표가 유효하지 않습니다", 
                                     {"x": location.x, "y": location.y})
        
        if not (-180 <= location.x <= 180) or not (-90 <= location.y <= 90):
            raise MatchingProcessError("request_validation", "위치 좌표가 범위를 벗어났습니다",
                                     {"x": location.x, "y": location.y})
        
        return location
        
    except Exception as e:
        raise MatchingProcessError("request_validation", f"요청 검증 중 오류: {str(e)}")

async def filter_by_time_preferences(
    caregivers: List[CaregiverForMatchingDTO],
    service_request: Any
) -> List[CaregiverForMatchingDTO]:
    """선호시간대 필터링: 신청자 선호시간대와 요양보호사 근무시간대 겹침 확인"""
    try:
        if not caregivers:
            raise MatchingProcessError("time_preference_filtering", "요양보호사 후보군이 제공되지 않았습니다")
        
        # 신청자의 선호시간대 추출
        preferred_start_time = getattr(service_request, 'preferredStartTime', None)
        preferred_end_time = getattr(service_request, 'preferredEndTime', None)
        
        # 요양보호사 정보를 딕셔너리 리스트로 변환
        caregiver_dicts = []
        for caregiver in caregivers:
            caregiver_dict = {
                'caregiver_id': caregiver.caregiverId,
                'work_start_time': getattr(caregiver, 'workStartTime', None),
                'work_end_time': getattr(caregiver, 'workEndTime', None),
                'base_location': caregiver.baseLocation,
                'career_years': caregiver.careerYears or 0,
                'work_area': caregiver.workArea
            }
            caregiver_dicts.append(caregiver_dict)
        
        # 시간대 필터링 적용
        filtered_caregivers = filter_caregivers_by_time_preference(
            caregiver_dicts, preferred_start_time, preferred_end_time
        )
        
        # 필터링된 요양보호사 DTO로 변환
        filtered_dtos = []
        for caregiver_dict in filtered_caregivers:
            caregiver_dto = CaregiverForMatchingDTO(
                caregiverId=caregiver_dict['caregiver_id'],
                baseLocation=caregiver_dict['base_location'],
                careerYears=caregiver_dict['career_years'],
                workArea=caregiver_dict['work_area'],
                workStartTime=caregiver_dict['work_start_time'],
                workEndTime=caregiver_dict['work_end_time']
            )
            filtered_dtos.append(caregiver_dto)
        
        logger.info(f"시간대 필터링 완료: 전체 {len(caregivers)}명 중 {len(filtered_dtos)}명 통과")
        return filtered_dtos
        
    except Exception as e:
        raise MatchingProcessError("time_preference_filtering", f"선호시간대 필터링 중 오류: {str(e)}")

async def load_nearby_caregivers(
    service_location: LocationInfo,
    all_caregivers: List[CaregiverForMatchingDTO]
) -> List[Tuple[CaregiverForMatching, float]]:
    """반경 15km 내 요양보호사 근거리 후보군 로드"""
    try:
        if not all_caregivers:
            raise MatchingProcessError("radius_filtering", "요양보호사 후보군이 제공되지 않았습니다")
        
        # DTO를 모델로 변환
        caregivers_models = []
        for dto in all_caregivers:
            caregiver_model = CaregiverForMatching(
                caregiver_id=dto.caregiverId,
                base_location=dto.baseLocation,
                career_years=dto.careerYears or 0,
                work_area=dto.workArea
            )
            caregivers_models.append(caregiver_model)
        
        # 15km 반경 내 필터링
        filtered_caregivers = filter_caregivers_by_distance(
            service_location, 
            caregivers_models, 
            radius_km=15.0
        )
        
        logger.info(f"전체 {len(all_caregivers)}명 중 15km 반경 내 {len(filtered_caregivers)}명 필터링")
        
        return filtered_caregivers
        
    except Exception as e:
        raise MatchingProcessError("radius_filtering", f"근거리 후보군 로드 중 오류: {str(e)}")

async def filter_by_preferences(
    nearby_candidates: List[Tuple[CaregiverForMatching, float]], 
    request: MatchingRequestDTO
) -> List[Tuple[CaregiverForMatching, float]]:
    """LLM 선호조건 변환 및 필터링으로 조건부합 후보군 생성"""
    try:
        logger.info(f"LLM 선호조건 필터링 시작: {len(nearby_candidates)}명의 후보군")
        
        qualified_candidates = []
        
        for caregiver, distance in nearby_candidates:
            try:
                # 요양보호사의 선호조건이 있는 경우에만 LLM 변환 수행
                if hasattr(caregiver, 'preferences_text') and caregiver.preferences_text:
                    logger.info(f"요양보호사 ID {caregiver.caregiver_id}의 선호조건 분석 중")
                    
                    # LLM 서비스 호출하여 비정형 텍스트를 정형 데이터로 변환
                    convert_request = ConvertNonStructuredDataToStructuredDataRequest(
                        non_structured_data=caregiver.preferences_text
                    )
                    structured_preferences = await convert_non_structured_data_to_structured_data(convert_request)
                    
                    # 기본적인 매칭 로직 (예시)
                    is_qualified = await evaluate_caregiver_match(
                        caregiver, structured_preferences, request
                    )
                    
                    if is_qualified:
                        qualified_candidates.append((caregiver, distance))
                        logger.info(f"요양보호사 ID {caregiver.caregiver_id} 조건 부합 - 선정")
                    else:
                        logger.info(f"요양보호사 ID {caregiver.caregiver_id} 조건 불일치 - 제외")
                else:
                    # 선호조건이 없는 경우 기본적으로 통과
                    qualified_candidates.append((caregiver, distance))
                    logger.info(f"요양보호사 ID {caregiver.caregiver_id} 선호조건 없음 - 기본 선정")
                    
            except Exception as e:
                logger.warning(f"요양보호사 ID {caregiver.caregiver_id} 필터링 중 오류: {str(e)} - 기본 선정")
                # 오류 발생 시 기본적으로 통과
                qualified_candidates.append((caregiver, distance))
        
        logger.info(f"LLM 선호조건 필터링 완료: {len(qualified_candidates)}명 선정")
        return qualified_candidates
        
    except Exception as e:
        raise MatchingProcessError("preference_filtering", f"선호조건 필터링 중 오류: {str(e)}")

async def evaluate_caregiver_match(
    caregiver: CaregiverForMatching, 
    structured_preferences: Any,
    request: MatchingRequestDTO
) -> bool:
    """요양보호사의 선호조건과 서비스 요청을 매칭하여 적합성 평가"""
    try:
        # 기본적인 매칭 로직 구현
        # 실제로는 더 복잡한 비즈니스 로직이 필요할 수 있음
        
        # 1. 서비스 유형 매칭 (예시)
        # if structured_preferences.service_types:
        #     # 서비스 요청의 서비스 유형과 매칭
        #     pass
        
        # 2. 근무 지역 매칭 (예시)
        # if structured_preferences.work_area:
        #     # 서비스 요청 위치와 선호 지역 매칭
        #     pass
        
        # 3. 근무 시간 매칭 (예시)
        # if structured_preferences.work_start_time and structured_preferences.work_end_time:
        #     # 요청된 서비스 시간과 근무 가능 시간 매칭
        #     pass
        
        # 현재는 기본적으로 모든 요양보호사를 적합하다고 판단 (임시)
        # 향후 비즈니스 요구사항에 따라 상세한 매칭 로직 구현 예정
        logger.debug(f"요양보호사 {caregiver.caregiver_id} 매칭 평가 완료")
        return True
        
    except Exception as e:
        logger.warning(f"매칭 평가 중 오류: {str(e)}")
        # 오류 발생 시 기본적으로 적합하다고 판단
        return True

async def calculate_travel_times(
    qualified_candidates: List[Tuple[CaregiverForMatching, float]], 
    service_location: LocationInfo
) -> List[Tuple[CaregiverForMatching, int, float]]:
    """네이버 Direction 5 API를 사용한 실제 ETA 계산"""
    try:
        eta_calculated_candidates = []
        
        # 요양보호사 위치들을 추출
        caregiver_locations = []
        for caregiver, distance_km in qualified_candidates:
            caregiver_locations.append(caregiver.base_location)
        
        logger.info(f"네이버 Direction API로 {len(caregiver_locations)}명의 ETA 계산 시작")
        
        # 배치 ETA 계산 (요양보호사 위치 → 서비스 요청 위치)
        eta_results = await eta_calculator.batch_calculate_eta(
            origins=caregiver_locations,
            destination=service_location
        )
        
        # 결과 조합
        for (caregiver, distance_km), eta_minutes in zip(qualified_candidates, eta_results):
            eta_calculated_candidates.append((caregiver, eta_minutes, distance_km))
        
        logger.info(f"네이버 Direction API ETA 계산 완료: {len(eta_calculated_candidates)}명")
        
        # 로깅으로 ETA 결과 확인
        for i, (caregiver, eta, distance) in enumerate(eta_calculated_candidates, 1):
            logger.info(f"  {i}. {caregiver.caregiver_id}: ETA {eta}분 (거리: {distance:.2f}km)")
        
        return eta_calculated_candidates
        
    except Exception as e:
        logger.error(f"ETA 계산 중 오류 발생: {str(e)}")
        # Fallback: 기존 거리 기반 계산
        logger.warning("Fallback으로 거리 기반 ETA 계산 사용")
        
        eta_calculated_candidates = []
        for caregiver, distance_km in qualified_candidates:
            eta_minutes = calculate_estimated_travel_time(distance_km)
            eta_calculated_candidates.append((caregiver, eta_minutes, distance_km))
        
        return eta_calculated_candidates

async def select_final_candidates(
    eta_calculated_candidates: List[Tuple[CaregiverForMatching, int, float]]
) -> List[Tuple[CaregiverForMatching, int, float]]:
    """ETA 기준 정렬 후 최종 5명 선정"""
    try:
        # ETA 기준 오름차순 정렬
        sorted_candidates = sorted(eta_calculated_candidates, key=lambda x: x[1])
        
        # 최대 5명 선정
        final_candidates = sorted_candidates[:5]
        
        logger.info(f"ETA 기준 최종 {len(final_candidates)}명 선정")
        for i, (caregiver, eta, distance) in enumerate(final_candidates, 1):
            logger.info(f"{i}순위: {caregiver.caregiver_id} (ETA: {eta}분, 거리: {distance:.2f}km)")
        
        return final_candidates
        
    except Exception as e:
        raise MatchingProcessError("final_selection", f"최종 후보 선정 중 오류: {str(e)}")

async def create_response_dtos(
    final_matches: List[Tuple[CaregiverForMatching, int, float]],
    original_caregivers: List[CaregiverForMatchingDTO]
) -> List[MatchedCaregiverDTO]:
    """최종 매칭 결과를 DTO로 변환"""
    try:
        matched_caregiver_dtos = []
        
        for i, (caregiver, eta_minutes, distance_km) in enumerate(final_matches, 1):
            # 원본 요양보호사 DTO 데이터 찾기
            caregiver_dto = next(
                (c for c in original_caregivers if c.caregiverId == caregiver.caregiver_id),
                None
            )
            
            if caregiver_dto:
                matched_dto = MatchedCaregiverDTO(
                    caregiverId=caregiver_dto.caregiverId,
                    availableTimes=caregiver_dto.availableTimes,
                    address=caregiver_dto.address,
                    location=caregiver_dto.baseLocation,
                    matchScore=float(10 - i),  # 1위: 9점, 2위: 8점, ... 5위: 5점
                    matchReason=f"{i}순위 | ETA {eta_minutes}분 | 거리 {distance_km}km",
                    distanceKm=distance_km,
                    estimatedTravelTime=eta_minutes,
                    career=caregiver_dto.career,
                    serviceType=caregiver_dto.serviceType,
                    isVerified=caregiver_dto.isVerified
                )
                matched_caregiver_dtos.append(matched_dto)
        
        return matched_caregiver_dtos
        
    except Exception as e:
        raise MatchingProcessError("response_creation", f"응답 DTO 생성 중 오류: {str(e)}")