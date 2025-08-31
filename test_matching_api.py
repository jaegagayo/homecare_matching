#!/usr/bin/env python3
"""
매칭 API 엔드포인트 테스트 스크립트
recommend API가 제대로 작동하는지 확인합니다.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.dto.matching import MatchingRequestDTO, ServiceRequestDTO, MatchingResponseDTO
from app.api.matching import recommend_matching

# 테스트 데이터
SAMPLE_SERVICE_REQUEST = {
    "serviceRequestId": "test-req-001",
    "consumerId": "consumer-001", 
    "serviceAddress": "서울특별시 강남구 테헤란로 123",
    "addressType": "상세주소",
    "location": "37.5013,127.0395",  # 강남역 좌표
    "requestDate": "2025-08-31",
    "preferredStartTime": "09:00",
    "preferredEndTime": "17:00",
    "duration": "8시간",
    "serviceType": "방문요양",
    "additionalInformation": "거동 불편한 고령자 돌봄 서비스 필요"
}

async def test_recommend_api():
    """recommend API 엔드포인트 테스트"""
    print("=" * 80)
    print("홈케어 매칭 API 테스트 시작")
    print("=" * 80)
    
    try:
        # 1. ServiceRequestDTO 생성 및 검증
        print("\n1. ServiceRequestDTO 생성 및 검증")
        service_request = ServiceRequestDTO(**SAMPLE_SERVICE_REQUEST)
        print(f"✅ ServiceRequestDTO 생성 성공")
        print(f"   서비스 요청 ID: {service_request.serviceRequestId}")
        print(f"   소비자 ID: {service_request.consumerId}")
        print(f"   위치: {service_request.location}")
        print(f"   선호 시간: {service_request.preferredStartTime} - {service_request.preferredEndTime}")
        
        # 2. MatchingRequestDTO 생성
        print("\n2. MatchingRequestDTO 생성")
        matching_request = MatchingRequestDTO(serviceRequest=service_request)
        print(f"✅ MatchingRequestDTO 생성 성공")
        
        # 3. recommend API 호출
        print("\n3. recommend API 호출")
        print("매칭 처리 시작...")
        start_time = datetime.now()
        
        try:
            response = await recommend_matching(matching_request)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            print(f"✅ recommend API 호출 성공")
            print(f"   처리 시간: {processing_time:.0f}ms")
            
            # 4. 응답 결과 검증
            print("\n4. 응답 결과 검증")
            print(f"   서비스 요청 ID: {response.serviceRequestId}")
            print(f"   매칭된 요양보호사 수: {response.matchedCount}")
            print(f"   전체 후보자 수: {response.totalCandidates}")
            print(f"   API 처리 시간: {response.processingTimeMs}ms")
            
            # 5. 최대 5명 제한 확인
            print(f"\n5. 최대 5명 제한 확인")
            if response.matchedCount <= 5:
                print(f"✅ 최대 5명 제한 준수: {response.matchedCount}명")
            else:
                print(f"❌ 최대 5명 제한 위반: {response.matchedCount}명")
            
            # 6. 매칭된 요양보호사 정보 출력
            print(f"\n6. 매칭된 요양보호사 정보")
            for i, caregiver in enumerate(response.matchedCaregivers, 1):
                print(f"   {i}순위:")
                print(f"     - ID: {caregiver.caregiverId}")
                print(f"     - 이름: {caregiver.name}")
                print(f"     - 거리: {caregiver.distanceKm:.2f}km")
                print(f"     - 예상 소요시간: {caregiver.estimatedTravelTime}분")
                print(f"     - 매칭 점수: {caregiver.matchScore}")
                print(f"     - 주소: {caregiver.address}")
                print(f"     - 위치: {caregiver.location}")
            
            # 7. 응답 형식 완성도 검증
            print(f"\n7. 응답 형식 완성도 검증")
            all_fields_complete = True
            for i, caregiver in enumerate(response.matchedCaregivers, 1):
                required_fields = ['caregiverId', 'distanceKm', 'matchScore']
                missing_fields = []
                
                for field in required_fields:
                    if getattr(caregiver, field) is None:
                        missing_fields.append(field)
                        all_fields_complete = False
                
                if missing_fields:
                    print(f"   ❌ {i}순위 요양보호사 필수 필드 누락: {missing_fields}")
            
            if all_fields_complete:
                print(f"   ✅ 모든 요양보호사의 필수 필드가 완성됨")
            
            return True
            
        except Exception as api_error:
            print(f"❌ recommend API 호출 실패: {str(api_error)}")
            print(f"   오류 유형: {type(api_error).__name__}")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {str(e)}")
        print(f"   오류 유형: {type(e).__name__}")
        return False

async def test_edge_cases():
    """경계 조건 테스트"""
    print("\n" + "=" * 80)
    print("경계 조건 테스트")
    print("=" * 80)
    
    # 1. 위치 정보 없는 경우
    print("\n1. 위치 정보 없는 요청 테스트")
    try:
        invalid_request = SAMPLE_SERVICE_REQUEST.copy()
        invalid_request["location"] = ""
        
        service_request = ServiceRequestDTO(**invalid_request)
        matching_request = MatchingRequestDTO(serviceRequest=service_request)
        
        response = await recommend_matching(matching_request)
        print("❌ 빈 위치 정보로도 API 호출이 성공함 (예상되지 않은 동작)")
        
    except Exception as e:
        print(f"✅ 빈 위치 정보 요청이 적절히 거부됨: {type(e).__name__}")
    
    # 2. 시간 정보 없는 경우  
    print("\n2. 선호 시간 정보 없는 요청 테스트")
    try:
        no_time_request = SAMPLE_SERVICE_REQUEST.copy()
        no_time_request["preferredStartTime"] = None
        no_time_request["preferredEndTime"] = None
        
        service_request = ServiceRequestDTO(**no_time_request)
        matching_request = MatchingRequestDTO(serviceRequest=service_request)
        
        response = await recommend_matching(matching_request)
        print(f"✅ 시간 정보 없는 요청 처리 성공: {response.matchedCount}명 매칭")
        
    except Exception as e:
        print(f"⚠️  시간 정보 없는 요청 실패: {type(e).__name__}: {str(e)}")

async def main():
    """메인 테스트 함수"""
    print("홈케어 매칭 API 테스트")
    print("Docker Compose로 전체 서비스를 실행해주세요:")
    print("cd /Users/jaehun/gh/jaegagayo/homecare_infra/code")
    print("docker compose up -d")
    print()
    
    # 기본 API 테스트
    success = await test_recommend_api()
    
    # 경계 조건 테스트
    await test_edge_cases()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 매칭 API 테스트가 성공적으로 완료되었습니다!")
        print("recommend API가 ServiceRequestDTO를 받아 최대 5명의 요양보호사를 반환합니다.")
    else:
        print("💡 매칭 API 테스트 실패")
        print("데이터베이스 연결 및 필요한 데이터가 있는지 확인해주세요.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())