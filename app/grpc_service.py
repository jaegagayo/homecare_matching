import logging
import asyncio
import time
from typing import List
from concurrent.futures import ThreadPoolExecutor

import grpc
from .grpc_generated import matching_service_pb2, matching_service_pb2_grpc

# 기존 매칭 API import
from .api.matching import recommend_matching
from .dto.matching import MatchingRequestDTO, CaregiverForMatchingDTO, ServiceRequestDTO

logger = logging.getLogger(__name__)

class MatchingServiceServicer(matching_service_pb2_grpc.MatchingServiceServicer):
    """gRPC 매칭 서비스 구현"""
    
    async def GetMatchingRecommendations(self, request, context):
        """매칭 추천 요청 처리"""
        start_time = time.time()
        
        try:
            logger.info(f"gRPC 매칭 요청 받음 - 서비스 요청 ID: {request.service_request.service_request_id}")
            
            # gRPC 요청을 내부 DTO로 변환
            service_request_dto = self._convert_grpc_service_request_to_dto(request.service_request)
            candidate_caregivers_dto = self._convert_grpc_caregivers_to_dto(request.candidate_caregivers)
            
            if not candidate_caregivers_dto:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("요양보호사 후보군이 제공되지 않았습니다")
                return matching_service_pb2.MatchingResponse(
                    success=False,
                    error_message="요양보호사 후보군이 제공되지 않았습니다"
                )
            
            # MatchingRequestDTO 생성
            matching_request = MatchingRequestDTO(
                serviceRequest=service_request_dto,
                candidateCaregivers=candidate_caregivers_dto
            )
            
            # 기존 HTTP API 호출
            matching_response = await recommend_matching(matching_request)
            
            # 매칭 결과를 gRPC 응답으로 변환
            grpc_matched_caregivers = []
            for matched_dto in matching_response.matchedCaregivers:
                grpc_caregiver = self._convert_matched_caregiver_dto_to_grpc(matched_dto)
                grpc_matched_caregivers.append(grpc_caregiver)
            
            processing_time = (time.time() - start_time) * 1000  # 밀리초
            
            response = matching_service_pb2.MatchingResponse(
                matched_caregivers=grpc_matched_caregivers,
                total_matches=len(grpc_matched_caregivers),
                processing_time_ms=f"{processing_time:.2f}ms",
                processing_results=str(matching_response.processingResults),
                success=True,
                error_message=""
            )
            
            logger.info(f"gRPC 매칭 완료 - 선택된 요양보호사: {len(grpc_matched_caregivers)}명, 처리시간: {processing_time:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"gRPC 매칭 처리 중 오류 발생: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"매칭 처리 중 오류가 발생했습니다: {str(e)}")
            return matching_service_pb2.MatchingResponse(
                success=False,
                error_message=f"매칭 처리 중 오류가 발생했습니다: {str(e)}"
            )
    
    def HealthCheck(self, request, context):
        """헬스체크 요청 처리"""
        try:
            logger.info("gRPC 헬스체크 요청 받음")
            return matching_service_pb2.HealthCheckResponse(
                status=matching_service_pb2.HealthCheckResponse.SERVING,
                message="Homecare Matching gRPC Service is running"
            )
        except Exception as e:
            logger.error(f"gRPC 헬스체크 중 오류 발생: {str(e)}")
            return matching_service_pb2.HealthCheckResponse(
                status=matching_service_pb2.HealthCheckResponse.NOT_SERVING,
                message=f"Service error: {str(e)}"
            )
    
    def _convert_grpc_service_request_to_dto(self, grpc_request) -> ServiceRequestDTO:
        """gRPC ServiceRequest를 ServiceRequestDTO로 변환"""
        return ServiceRequestDTO(
            serviceRequestId=grpc_request.service_request_id,
            consumerId=grpc_request.consumer_id,
            serviceAddress=grpc_request.service_address,
            addressType=grpc_request.address_type or None,
            location=[grpc_request.location.latitude, grpc_request.location.longitude],
            preferredTime=grpc_request.preferred_time or None,
            duration=grpc_request.duration or None,
            serviceType=grpc_request.service_type or None,
            requestStatus=grpc_request.request_status or "PENDING",
            requestDate=grpc_request.request_date or None,
            additionalInformation=grpc_request.additional_information or None
        )
    
    def _convert_grpc_caregivers_to_dto(self, grpc_caregivers) -> List[CaregiverForMatchingDTO]:
        """gRPC CaregiverForMatching 리스트를 CaregiverForMatchingDTO 리스트로 변환"""
        caregiver_dtos = []
        
        for grpc_caregiver in grpc_caregivers:
            caregiver_dto = CaregiverForMatchingDTO(
                caregiverId=grpc_caregiver.caregiver_id,
                userId=grpc_caregiver.user_id,
                availableTimes=grpc_caregiver.available_times or None,
                address=grpc_caregiver.address or None,
                serviceType=grpc_caregiver.service_type or None,
                daysOff=grpc_caregiver.days_off or None,
                career=grpc_caregiver.career or None,
                koreanProficiency=grpc_caregiver.korean_proficiency or None,
                isAccompanyOuting=grpc_caregiver.is_accompany_outing if hasattr(grpc_caregiver, 'is_accompany_outing') else None,
                selfIntroduction=grpc_caregiver.self_introduction or None,
                isVerified=grpc_caregiver.is_verified if hasattr(grpc_caregiver, 'is_verified') else None,
                baseLocation=[grpc_caregiver.base_location.latitude, grpc_caregiver.base_location.longitude],
                careerYears=grpc_caregiver.career_years,
                workDays=grpc_caregiver.work_days or None,
                workArea=grpc_caregiver.work_area or None,
                transportation=grpc_caregiver.transportation or None,
                supportedConditions=grpc_caregiver.supported_conditions or None
            )
            caregiver_dtos.append(caregiver_dto)
        
        return caregiver_dtos
    
    def _convert_matched_caregiver_dto_to_grpc(self, matched_dto):
        """매칭된 요양보호사 DTO를 gRPC 형태로 변환"""
        return matching_service_pb2.MatchedCaregiver(
            caregiver_id=matched_dto.caregiverId,
            available_times=matched_dto.availableTimes or "",
            address=matched_dto.address or "",
            location=matching_service_pb2.Location(
                latitude=matched_dto.location[0],
                longitude=matched_dto.location[1]
            ),
            match_score=matched_dto.matchScore,
            match_reason=matched_dto.matchReason,
            distance_km=matched_dto.distanceKm,
            estimated_travel_time=matched_dto.estimatedTravelTime,
            career=matched_dto.career or "",
            service_type=matched_dto.serviceType or "",
            is_verified=matched_dto.isVerified or False
        )

async def serve_grpc(port: int = 50051):
    """gRPC 서버 실행 (비동기)"""
    server = grpc.aio.server(ThreadPoolExecutor(max_workers=10))
    matching_service_pb2_grpc.add_MatchingServiceServicer_to_server(
        MatchingServiceServicer(), server
    )
    
    listen_addr = f'[::]:{port}'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"gRPC 서버 시작 - 포트: {port}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC 서버 종료 중...")
        await server.stop(5)