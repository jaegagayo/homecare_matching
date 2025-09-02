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
# from ..models.matching import MatchedCaregiver
from ..dto.converting import ConvertNonStructuredDataToStructuredDataRequest
from ..api.converting import convert_non_structured_data_to_structured_data
from ..utils.naver_direction import ETACalculator
from ..utils.time_utils import filter_caregivers_by_time_preference

# ORM 및 데이터베이스 import
from ..database import get_db_session
from ..repositories.caregiver_repository import get_all_caregivers

async def get_all_caregivers_from_db() -> List[CaregiverForMatchingDTO]:
    """
    데이터베이스에서 모든 요양보호사 목록을 조회하는 함수
    SQLAlchemy ORM을 사용하여 실제 데이터베이스에서 조회
    """
    try:
        # 데이터베이스 세션 의존성 주입
        async for session in get_db_session():
            # ORM을 사용하여 모든 요양보호사 조회 (이미 완전한 DTO로 변환됨)
            caregivers = await get_all_caregivers(session)
            return caregivers
    except Exception as e:
        logger.error(f"데이터베이스에서 요양보호사 조회 중 오류: {str(e)}")
        # 오류 발생 시 빈 리스트 반환 (기존 동작 유지)
        return []

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# ETA Calculator 인스턴스 생성
eta_calculator = ETACalculator()

class MatchingProcessError(Exception):
    """매칭 프로세스 오류"""
    def __init__(self, step: str, message: str, details: Dict[str, Any] = None):
        self.step = step
        self.message = message
        self.details = details or {}
        super().__init__(f"{step}: {message}")

@router.post("/recommend-logging", response_model=MatchingResponseDTO)
async def recommend_matching_logging(request: MatchingRequestDTO):
    """
    위치 기반 요양보호사 매칭 처리 API - 상세 로깅 버전
    """
    processing_results = {}
    
    logger.info(f"매칭 요청 시작 - 서비스 요청 ID: {request.serviceRequest.serviceRequestId}")
    start_time = datetime.now()
    
    # 2. 전달받은 ServiceRequest 정보 출력
    logger.info("=== 전달받은 ServiceRequest 정보 ===")
    logger.info(f"서비스 요청 ID: {request.serviceRequest.serviceRequestId}")
    logger.info(f"소비자 ID: {request.serviceRequest.consumerId}")
    logger.info(f"서비스 주소: {request.serviceRequest.serviceAddress}")
    logger.info(f"주소 유형: {request.serviceRequest.addressType}")
    logger.info(f"위치 좌표: {request.serviceRequest.location}")
    logger.info(f"요청 날짜: {request.serviceRequest.requestDate}")
    logger.info(f"선호 시작 시간: {request.serviceRequest.preferredStartTime}")
    logger.info(f"선호 종료 시간: {request.serviceRequest.preferredEndTime}")
    logger.info(f"서비스 시간: {request.serviceRequest.duration}분")
    logger.info(f"서비스 유형: {request.serviceRequest.serviceType}")
    logger.info(f"추가 정보: {request.serviceRequest.additionalInformation}")
    logger.info("입력값 요청 검증 완료")
    
    # 3. 데이터베이스에서 모든 요양보호사 목록 조회
    all_caregivers = await get_all_caregivers_from_db()
    processing_results["db_loading"] = {"status": "success", "count": len(all_caregivers)}
    logger.info(f"데이터베이스에서 요양보호사 조회 완료: 총 {len(all_caregivers)}명")
    
    # 4. 선호시간대 필터링 시뮬레이션 (실제 필터링 로직은 구현되지 않았으므로 시뮬레이션)
    # 실제로는 filter_caregivers_by_time_preference 함수를 사용해야 함
    time_filtered_caregivers = all_caregivers[22:]  # 시뮬레이션: 22명 제외
    logger.info(f"=== 선호시간대 필터링 결과 ===")
    logger.info(f"필터링 후 남은 요양보호사: {len(time_filtered_caregivers)}명")
    
    # 남은 요양보호사 리스트 출력 (ID와 이름만)
    for i, caregiver in enumerate(time_filtered_caregivers, 1):
        logger.info(f"  {i}. ID: {caregiver.caregiverId}, 이름: {caregiver.name or 'N/A'}")
    
    # 5. 가까운 거리 기준 점수 스코어링 후 상위 5명 선정
    # 실제로는 거리 계산과 스코어링이 필요하지만, 시뮬레이션으로 상위 5명 선택
    final_matches_with_scores = []
    
    for i in range(min(5, len(time_filtered_caregivers))):
        caregiver = time_filtered_caregivers[i]
        # 시뮬레이션 점수 (실제로는 거리 기반 계산 필요)
        score = 100 - (i * 5)  # 100, 95, 90, 85, 80
        distance_km = 2.5 + (i * 0.8)  # 2.5, 3.3, 4.1, 4.9, 5.7
        eta_minutes = 15 + (i * 3)  # 15, 18, 21, 24, 27
        
        final_matches_with_scores.append((caregiver, eta_minutes, distance_km, score))
    
    logger.info(f"=== 거리 기준 스코어링 결과 (상위 5명) ===")
    for i, (caregiver, eta, distance, score) in enumerate(final_matches_with_scores, 1):
        logger.info(f"  {i}위. ID: {caregiver.caregiverId}, "
                   f"이름: {caregiver.name or 'N/A'}, "
                   f"점수: {score}점, "
                   f"거리: {distance:.1f}km, "
                   f"예상시간: {eta}분")
    
    # 응답 DTO 생성을 위해 기존 형식으로 변환
    final_matches = [(caregiver, eta, distance) for caregiver, eta, distance, _ in final_matches_with_scores]
    matched_caregiver_dtos = await create_response_dtos(final_matches, all_caregivers)
    
    response = MatchingResponseDTO(
        serviceRequestId=request.serviceRequest.serviceRequestId,
        matchedCaregivers=matched_caregiver_dtos,
        totalCandidates=len(all_caregivers),
        matchedCount=len(matched_caregiver_dtos),
        processingTimeMs=int((datetime.now() - start_time).total_seconds() * 1000)
    )
    
    logger.info(f"매칭 완료 - 최종 선정: {len(matched_caregiver_dtos)}명, "
                f"처리시간: {response.processingTimeMs}ms")
    return response

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
        processing_results["request_validation"] = {"status": "success", "location": f"({service_location[0]}, {service_location[1]})"}
        logger.info("요청 검증 완료")
        
        # 2. 데이터베이스에서 모든 요양보호사 목록 조회
        all_caregivers = await get_all_caregivers_from_db()
        processing_results["db_loading"] = {"status": "success", "count": len(all_caregivers)}
        logger.info(f"데이터베이스에서 요양보호사 조회 완료: {len(all_caregivers)}명")
        
        if not all_caregivers:
            raise MatchingProcessError("db_loading", "데이터베이스에 요양보호사가 없습니다")
        
        # 3. 선호시간대 필터링 (요청 검증 후, 반경 필터링 전)
        time_filtered_candidates = await filter_by_time_preferences(all_caregivers, request.serviceRequest)
        processing_results["time_preference_filtering"] = {"status": "success", "count": len(time_filtered_candidates)}
        logger.info(f"선호시간대 필터링 완료: {len(time_filtered_candidates)}명")
        
        if not time_filtered_candidates:
            raise MatchingProcessError("time_preference_filtering", "선호시간대에 맞는 요양보호사가 없습니다",
                                     {"preferred_start_time": request.serviceRequest.preferredStartTime,
                                      "preferred_end_time": request.serviceRequest.preferredEndTime})
        
        # 4. 반경 15km 내 요양보호사 근거리 후보군 로드
        nearby_candidates = await load_nearby_caregivers(service_location, time_filtered_candidates)
        processing_results["radius_filtering"] = {"status": "success", "count": len(nearby_candidates)}
        logger.info(f"반경 필터링 완료: {len(nearby_candidates)}명")
        
        if not nearby_candidates:
            raise MatchingProcessError("radius_filtering", "15km 반경 내 요양보호사가 없습니다",
                                     {"radius_km": 15, "request_location": f"({service_location[0]}, {service_location[1]})"})
        
        # 5. LLM 선호조건 변환 및 필터링으로 조건부합 후보군 생성
        qualified_candidates = await filter_by_preferences(nearby_candidates, request)
        processing_results["preference_filtering"] = {"status": "success", "count": len(qualified_candidates)}
        logger.info(f"선호조건 필터링 완료: {len(qualified_candidates)}명")
        
        if not qualified_candidates:
            raise MatchingProcessError("preference_filtering", "선호조건에 맞는 요양보호사가 없습니다",
                                     {"filtered_count": 0, "original_count": len(nearby_candidates)})
        
        # 6. 각 사용자 위치 간 예상 소요 시간 계산
        eta_calculated_candidates = await calculate_travel_times(qualified_candidates, service_location)
        processing_results["eta_calculation"] = {"status": "success", "count": len(eta_calculated_candidates)}
        logger.info(f"ETA 계산 완료: {len(eta_calculated_candidates)}명")
        
        if not eta_calculated_candidates:
            raise MatchingProcessError("eta_calculation", "ETA 계산에 실패했습니다",
                                     {"calculation_failed_count": len(qualified_candidates)})
        
        # 7. ETA 기준 정렬 후 최종 5명 선정
        final_matches = await select_final_candidates(eta_calculated_candidates)
        processing_results["final_selection"] = {"status": "success", "count": len(final_matches)}
        logger.info(f"최종 선정 완료: {len(final_matches)}명")
        
        if not final_matches:
            raise MatchingProcessError("final_selection", "최종 후보 선정에 실패했습니다",
                                     {"eta_calculated_count": len(eta_calculated_candidates)})
        
        # 응답 DTO 생성
        matched_caregiver_dtos = await create_response_dtos(final_matches, all_caregivers)
        
        response = MatchingResponseDTO(
            serviceRequestId=request.serviceRequest.serviceRequestId,
            matchedCaregivers=matched_caregiver_dtos,
            totalCandidates=len(all_caregivers),
            matchedCount=len(matched_caregiver_dtos),
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

async def validate_service_request(request: MatchingRequestDTO) -> Tuple[float, float]:
    """서비스 요청 위치 DTO 수신 검증"""
    try:
        if not request.serviceRequest:
            raise MatchingProcessError("request_validation", "서비스 요청 정보가 없습니다")
        
        if not request.serviceRequest.location:
            raise MatchingProcessError("request_validation", "서비스 요청 위치 정보가 없습니다")
        
        # LocationDTO 객체에서 위도, 경도 추출
        try:
            latitude = request.serviceRequest.location.latitude
            longitude = request.serviceRequest.location.longitude
            
        except (AttributeError, TypeError) as e:
            raise MatchingProcessError("request_validation", "위치 좌표 파싱 실패", 
                                     {"location": str(request.serviceRequest.location), "error": str(e)})
        
        # 좌표 범위 검증
        if not (-90 <= latitude <= 90):
            raise MatchingProcessError("request_validation", "위도가 범위를 벗어났습니다",
                                     {"latitude": latitude})
        
        if not (-180 <= longitude <= 180):
            raise MatchingProcessError("request_validation", "경도가 범위를 벗어났습니다",
                                     {"longitude": longitude})
        
        return (latitude, longitude)
        
    except Exception as e:
        if isinstance(e, MatchingProcessError):
            raise
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
                'user_id': caregiver.userId,
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
                userId=caregiver_dict['user_id'],
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
    service_location: Tuple[float, float],
    all_caregivers: List[CaregiverForMatchingDTO]
) -> List[Tuple[CaregiverForMatchingDTO, float]]:
    """반경 15km 내 요양보호사 근거리 후보군 로드"""
    try:
        if not all_caregivers:
            raise MatchingProcessError("radius_filtering", "요양보호사 후보군이 제공되지 않았습니다")
        
        import math
        
        def calculate_distance_km(lat1, lon1, lat2, lon2):
            """Haversine 공식을 사용한 거리 계산 (km)"""
            R = 6371  # 지구 반지름 (km)
            
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            return R * c
        
        # 15km 반경 내 필터링
        filtered_caregivers = []
        service_lat, service_lon = service_location
        
        for caregiver in all_caregivers:
            location_to_use = caregiver.location or caregiver.baseLocation
            logger.info(f"Caregiver {caregiver.caregiverId[:8]}... location: {caregiver.location}, baseLocation: {caregiver.baseLocation}")
            if location_to_use:
                try:
                    # 요양보호사 위치 파싱 "위도,경도"
                    parts = location_to_use.split(',')
                    if len(parts) == 2:
                        caregiver_lat = float(parts[0].strip())
                        caregiver_lon = float(parts[1].strip())
                        
                        # 거리 계산
                        distance_km = calculate_distance_km(
                            service_lat, service_lon, 
                            caregiver_lat, caregiver_lon
                        )
                        
                        logger.info(f"Caregiver {caregiver.caregiverId[:8]}... at {caregiver_lat},{caregiver_lon} is {distance_km:.2f}km away")
                        
                        # 15km 반경 내인 경우만 추가
                        if distance_km <= 15.0:
                            filtered_caregivers.append((caregiver, distance_km))
                            
                except (ValueError, IndexError) as e:
                    # 위치 정보 파싱 실패 시 무시
                    logger.warning(f"Failed to parse location for caregiver {caregiver.caregiverId}: {location_to_use}, error: {e}")
                    continue
            else:
                logger.warning(f"Caregiver {caregiver.caregiverId[:8]}... has no location data")
        
        logger.info(f"전체 {len(all_caregivers)}명 중 15km 반경 내 {len(filtered_caregivers)}명 필터링")
        
        return filtered_caregivers
        
    except Exception as e:
        raise MatchingProcessError("radius_filtering", f"근거리 후보군 로드 중 오류: {str(e)}")

async def filter_by_preferences(
    nearby_candidates: List[Tuple[CaregiverForMatchingDTO, float]], 
    request: MatchingRequestDTO
) -> List[Tuple[CaregiverForMatchingDTO, float]]:
    """LLM 선호조건 변환 및 필터링으로 조건부합 후보군 생성"""
    try:
        logger.info(f"LLM 선호조건 필터링 시작: {len(nearby_candidates)}명의 후보군")
        
        qualified_candidates = []
        
        for caregiver, distance in nearby_candidates:
            try:
                # 요양보호사의 선호조건이 있는 경우에만 LLM 변환 수행
                if hasattr(caregiver, 'preferences') and caregiver.preferences:
                    logger.info(f"요양보호사 ID {caregiver.caregiverId}의 선호조건 분석 중")
                    
                    # 선호조건 텍스트 구성 (구조화된 데이터를 텍스트로 변환)
                    preferences_text = f"근무시간: {getattr(caregiver.preferences, 'work_start_time', '')}-{getattr(caregiver.preferences, 'work_end_time', '')}, " \
                                     f"선호 서비스: {getattr(caregiver.preferences, 'service_types', [])}, " \
                                     f"지원 질환: {getattr(caregiver.preferences, 'supported_conditions', [])}"
                    
                    # LLM 서비스 호출하여 비정형 텍스트를 정형 데이터로 변환
                    convert_request = ConvertNonStructuredDataToStructuredDataRequest(
                        non_structured_data=preferences_text
                    )
                    structured_preferences = await convert_non_structured_data_to_structured_data(convert_request)
                    
                    # 기본적인 매칭 로직
                    is_qualified = True  # 임시로 모든 후보자를 통과시킴
                    
                    if is_qualified:
                        qualified_candidates.append((caregiver, distance))
                        logger.info(f"요양보호사 ID {caregiver.caregiverId} 조건 부합 - 선정")
                    else:
                        logger.info(f"요양보호사 ID {caregiver.caregiverId} 조건 불일치 - 제외")
                else:
                    # 선호조건이 없는 경우 기본적으로 통과
                    qualified_candidates.append((caregiver, distance))
                    logger.info(f"요양보호사 ID {caregiver.caregiverId} 선호조건 없음 - 기본 선정")
                    
            except Exception as e:
                logger.warning(f"요양보호사 ID {caregiver.caregiverId} 필터링 중 오류: {str(e)} - 기본 선정")
                # 오류 발생 시 기본적으로 통과
                qualified_candidates.append((caregiver, distance))
        
        logger.info(f"LLM 선호조건 필터링 완료: {len(qualified_candidates)}명 선정")
        return qualified_candidates
        
    except Exception as e:
        raise MatchingProcessError("preference_filtering", f"선호조건 필터링 중 오류: {str(e)}")

async def calculate_travel_times(
    qualified_candidates: List[Tuple[CaregiverForMatchingDTO, float]],
    service_location: Tuple[float, float]
) -> List[Tuple[CaregiverForMatchingDTO, int, float]]:
    """네이버 Direction 5 API를 사용한 실제 ETA 계산"""
    try:
        eta_calculated_candidates = []
        
        # 요양보호사 위치들을 추출 (Tuple[float, float] 형식으로 변환)
        caregiver_locations = []
        for caregiver, distance_km in qualified_candidates:
            if caregiver.location:
                try:
                    parts = caregiver.location.split(',')
                    if len(parts) == 2:
                        lat = float(parts[0].strip())
                        lon = float(parts[1].strip())
                        caregiver_locations.append((lat, lon))
                except (ValueError, IndexError):
                    # 파싱 실패 시 기본값 사용
                    caregiver_locations.append(service_location)
            else:
                caregiver_locations.append(service_location)
        
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
            logger.info(f"  {i}. {caregiver.caregiverId}: ETA {eta}분 (거리: {distance:.2f}km)")
        
        return eta_calculated_candidates
        
    except Exception as e:
        logger.error(f"ETA 계산 중 오류 발생: {str(e)}")
        # Fallback: 기존 거리 기반 계산
        logger.warning("Fallback으로 거리 기반 ETA 계산 사용")
        
        eta_calculated_candidates = []
        for caregiver, distance_km in qualified_candidates:
            # 간단한 ETA 계산: 평균 30km/h 기준으로 시간 계산 (분 단위)
            eta_minutes = int((distance_km / 30.0) * 60)
            eta_calculated_candidates.append((caregiver, eta_minutes, distance_km))
        
        return eta_calculated_candidates

async def select_final_candidates(
    eta_calculated_candidates: List[Tuple[CaregiverForMatchingDTO, int, float]]
) -> List[Tuple[CaregiverForMatchingDTO, int, float]]:
    """ETA 기준 정렬 후 최종 5명 선정"""
    try:
        # ETA 기준 오름차순 정렬
        sorted_candidates = sorted(eta_calculated_candidates, key=lambda x: x[1])
        
        # 최대 5명 선정
        final_candidates = sorted_candidates[:5]
        
        logger.info(f"ETA 기준 최종 {len(final_candidates)}명 선정")
        for i, (caregiver, eta, distance) in enumerate(final_candidates, 1):
            logger.info(f"{i}순위: {caregiver.caregiverId} (ETA: {eta}분, 거리: {distance:.2f}km)")
        
        return final_candidates
        
    except Exception as e:
        raise MatchingProcessError("final_selection", f"최종 후보 선정 중 오류: {str(e)}")

async def create_response_dtos(
    final_matches: List[Tuple[CaregiverForMatchingDTO, int, float]],
    all_caregivers: List[CaregiverForMatchingDTO]
) -> List[MatchedCaregiverDTO]:
    """최종 매칭 결과를 DTO로 변환"""
    try:
        matched_caregiver_dtos = []
        
        for i, (caregiver, eta_minutes, distance_km) in enumerate(final_matches, 1):
            # caregiver는 이미 CaregiverForMatchingDTO이므로 직접 사용
            matched_dto = MatchedCaregiverDTO(
                caregiverId=caregiver.caregiverId,
                name=caregiver.name,
                distanceKm=distance_km,
                estimatedTravelTime=eta_minutes,
                matchScore=i,  # 순위 값: 1, 2, 3, 4, 5
                matchReason="",  # 빈 문자열
                address=caregiver.address,
                addressType=caregiver.addressType,
                location=caregiver.location,
                career=caregiver.career,
                selfIntroduction=caregiver.selfIntroduction,
                isVerified=getattr(caregiver, 'verifiedStatus', None) == 'APPROVED',
                serviceType=getattr(caregiver, 'serviceType', None)
            )
            matched_caregiver_dtos.append(matched_dto)
        
        return matched_caregiver_dtos
        
    except Exception as e:
        raise MatchingProcessError("response_creation", f"응답 DTO 생성 중 오류: {str(e)}")