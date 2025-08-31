#!/usr/bin/env python3
"""
gRPC 클라이언트 테스트 스크립트
매칭 서비스 gRPC 서버와 통신 테스트

⚠️  테스트 전에 gRPC 서버 포트를 확인하고 필요시 아래 GRPC_PORT 값을 수정하세요.
기본값은 50051이지만, Docker Compose나 다른 설정에 따라 다를 수 있습니다.
"""

import asyncio
import logging
import grpc
from app.grpc_generated import matching_service_pb2, matching_service_pb2_grpc

# gRPC 서버 포트 설정 (테스트 시 서버 설정에 맞게 수정 필요)
GRPC_PORT = 50051

async def test_health_check():
    """헬스체크 테스트"""
    try:
        async with grpc.aio.insecure_channel(f'localhost:{GRPC_PORT}') as channel:
            stub = matching_service_pb2_grpc.MatchingServiceStub(channel)
            
            request = matching_service_pb2.HealthCheckRequest(
                service="matching"
            )
            
            response = await stub.HealthCheck(request)
            
            print("✅ 헬스체크 성공:")
            print(f"   상태: {response.status}")
            print(f"   메시지: {response.message}")
            return True
            
    except Exception as e:
        print(f"❌ 헬스체크 실패: {e}")
        return False

async def test_matching_request():
    """매칭 요청 테스트"""
    try:
        async with grpc.aio.insecure_channel(f'localhost:{GRPC_PORT}') as channel:
            stub = matching_service_pb2_grpc.MatchingServiceStub(channel)
            
            # 테스트용 서비스 요청 생성
            service_request = matching_service_pb2.ServiceRequest(
                service_request_id="test-service-001",
                consumer_id="test-consumer-001",
                service_address="서울시 강남구 테헤란로 123",
                address_type="HOME",
                location=matching_service_pb2.Location(
                    latitude=37.5665,  # 강남역 근처
                    longitude=127.0780
                ),
                preferred_time="09:00-18:00",
                duration="4시간",
                service_type="방문요양",
                request_status="PENDING",
                additional_information="테스트 요청"
            )
            
            # 테스트용 요양보호사 후보 생성
            caregiver1 = matching_service_pb2.CaregiverForMatching(
                caregiver_id="caregiver-001",
                user_id="user-001",
                available_times="09:00-18:00",
                address="서울시 강남구 역삼동",
                service_type="방문요양",
                days_off="일요일",
                career="3년",
                korean_proficiency="상급",
                is_accompany_outing=True,
                is_verified=True,
                base_location=matching_service_pb2.Location(
                    latitude=37.5663,  # 강남역에서 가까운 위치
                    longitude=127.0779
                ),
                career_years=3,
                work_area="강남구",
                transportation="대중교통"
            )
            
            caregiver2 = matching_service_pb2.CaregiverForMatching(
                caregiver_id="caregiver-002",
                user_id="user-002",
                available_times="08:00-17:00",
                address="서울시 서초구 서초동",
                service_type="방문요양",
                days_off="토요일",
                career="5년",
                korean_proficiency="상급",
                is_accompany_outing=False,
                is_verified=True,
                base_location=matching_service_pb2.Location(
                    latitude=37.4833,  # 서초역 근처
                    longitude=127.0323
                ),
                career_years=5,
                work_area="서초구",
                transportation="자가용"
            )
            
            # 매칭 요청 생성
            matching_request = matching_service_pb2.MatchingRequest(
                service_request=service_request,
                candidate_caregivers=[caregiver1, caregiver2]
            )
            
            # 매칭 요청 전송
            response = await stub.GetMatchingRecommendations(matching_request)
            
            if response.success:
                print("✅ 매칭 요청 성공:")
                print(f"   매칭된 요양보호사 수: {response.total_matches}")
                print(f"   처리 시간: {response.processing_time_ms}")
                
                for i, caregiver in enumerate(response.matched_caregivers, 1):
                    print(f"\\n   {i}순위:")
                    print(f"     ID: {caregiver.caregiver_id}")
                    print(f"     점수: {caregiver.match_score}")
                    print(f"     거리: {caregiver.distance_km:.2f}km")
                    print(f"     매칭 이유: {caregiver.match_reason}")
                    print(f"     검증 상태: {'✓' if caregiver.is_verified else '✗'}")
                
                return True
            else:
                print(f"❌ 매칭 요청 실패: {response.error_message}")
                return False
                
    except Exception as e:
        print(f"❌ 매칭 요청 실패: {e}")
        return False

async def main():
    """메인 테스트 함수"""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 gRPC 서비스 테스트 시작")
    print("=" * 50)
    
    # 1. 헬스체크 테스트
    print("\\n1. 헬스체크 테스트")
    health_ok = await test_health_check()
    
    if not health_ok:
        print("\\n❌ 서버가 실행되지 않았거나 연결할 수 없습니다.")
        print("   다음 명령으로 서버를 먼저 실행해주세요:")
        print("   python run_server.py")
        return
    
    # 2. 매칭 요청 테스트
    print("\\n2. 매칭 요청 테스트")
    matching_ok = await test_matching_request()
    
    # 결과 요약
    print("\\n" + "=" * 50)
    print("🧪 테스트 결과:")
    print(f"   헬스체크: {'✅' if health_ok else '❌'}")
    print(f"   매칭 요청: {'✅' if matching_ok else '❌'}")
    
    if health_ok and matching_ok:
        print("\\n🎉 모든 테스트 통과! gRPC 서비스가 정상적으로 동작합니다.")
    else:
        print("\\n⚠️  일부 테스트 실패. 로그를 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(main())