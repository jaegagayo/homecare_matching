#!/usr/bin/env python3
"""
매칭 API HTTP 요청 테스트 스크립트
실제 HTTP 요청으로 API를 테스트합니다.
"""

import json
import requests
import time
from datetime import datetime

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/matching/recommend"

# 테스트 데이터 (api_test_data.json 내용을 직접 포함)
TEST_DATA = {
    "basic_request": {
        "serviceRequest": {
            "serviceRequestId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "consumerId": "b2c3d4e5-f6g7-8901-bcde-f12345678901",
            "serviceAddress": "서울특별시 강남구 테헤란로 123",
            "addressType": "ROAD",
            "location": {
                "latitude": 37.4979,
                "longitude": 127.0276
            },
            "requestDate": "2025-09-03",
            "preferredStartTime": "09:00:00",
            "preferredEndTime": "17:00:00",
            "duration": 480,
            "serviceType": "VISITING_CARE",
            "additionalInformation": "거동 불편한 고령자 돌봄 서비스 필요"
        }
    },
    "morning_service_request": {
        "serviceRequest": {
            "serviceRequestId": "c3d4e5f6-g7h8-9012-cdef-234567890123",
            "consumerId": "d4e5f6g7-h8i9-0123-defg-345678901234",
            "serviceAddress": "서울특별시 송파구 올림픽로 300",
            "addressType": "ROAD",
            "location": {
                "latitude": 37.5118,
                "longitude": 126.9876
            },
            "requestDate": "2025-09-04",
            "preferredStartTime": "08:00:00",
            "preferredEndTime": "12:00:00",
            "duration": 240,
            "serviceType": "VISITING_CARE",
            "additionalInformation": "오전 시간대 집중 케어 희망"
        }
    },
    "afternoon_service_request": {
        "serviceRequest": {
            "serviceRequestId": "e5f6g7h8-i9j0-1234-efgh-456789012345",
            "consumerId": "f6g7h8i9-j0k1-2345-fghi-567890123456",
            "serviceAddress": "서울특별시 서초구 강남대로 456",
            "addressType": "JIBUN",
            "location": {
                "latitude": 37.4847,
                "longitude": 127.0324
            },
            "requestDate": "2025-09-05",
            "preferredStartTime": "14:00:00",
            "preferredEndTime": "18:00:00",
            "duration": 240,
            "serviceType": "VISITING_CARE",
            "additionalInformation": "오후 시간대 서비스 필요"
        }
    },
    "full_day_service_request": {
        "serviceRequest": {
            "serviceRequestId": "g7h8i9j0-k1l2-3456-ghij-678901234567",
            "consumerId": "h8i9j0k1-l2m3-4567-hijk-789012345678",
            "serviceAddress": "서울특별시 마포구 월드컵로 789",
            "addressType": "ROAD",
            "location": {
                "latitude": 37.5567,
                "longitude": 126.9240
            },
            "requestDate": "2025-09-06",
            "preferredStartTime": "08:00:00",
            "preferredEndTime": "20:00:00",
            "duration": 720,
            "serviceType": "VISITING_CARE",
            "additionalInformation": "장시간 집중 돌봄 서비스 필요, 식사 준비 포함"
        }
    },
    "weekend_service_request": {
        "serviceRequest": {
            "serviceRequestId": "i9j0k1l2-m3n4-5678-ijkl-890123456789",
            "consumerId": "j0k1l2m3-n4o5-6789-jklm-901234567890",
            "serviceAddress": "서울특별시 용산구 한강대로 321",
            "addressType": "JIBUN",
            "location": {
                "latitude": 37.5326,
                "longitude": 126.9652
            },
            "requestDate": "2025-09-07",
            "preferredStartTime": "10:00:00",
            "preferredEndTime": "16:00:00",
            "duration": 360,
            "serviceType": "VISITING_CARE",
            "additionalInformation": "주말 시간대 서비스, 가족 방문 시간 고려"
        }
    }
}

def test_api_request(test_name, request_data):
    """API 요청 테스트"""
    print(f"\n{'='*60}")
    print(f"🧪 테스트: {test_name}")
    print(f"{'='*60}")
    
    try:
        # 요청 데이터 출력
        print("📤 요청 데이터:")
        print(json.dumps(request_data, indent=2, ensure_ascii=False))
        
        # API 호출
        start_time = time.time()
        response = requests.post(
            API_ENDPOINT,
            json=request_data,
            headers={
                'Content-Type': 'application/json',
                'accept': 'application/json'
            },
            timeout=30
        )
        end_time = time.time()
        
        # 응답 시간 계산
        response_time = (end_time - start_time) * 1000
        
        print(f"\n📊 응답 정보:")
        print(f"   - 상태 코드: {response.status_code}")
        print(f"   - 응답 시간: {response_time:.2f}ms")
        
        if response.status_code == 200:
            print("✅ 요청 성공!")
            
            # 응답 데이터 파싱
            response_data = response.json()
            
            print(f"\n📥 응답 데이터:")
            print(f"   - 서비스 요청 ID: {response_data.get('serviceRequestId', 'N/A')}")
            print(f"   - 전체 후보자 수: {response_data.get('totalCandidates', 'N/A')}")
            print(f"   - 매칭된 요양보호사 수: {response_data.get('matchedCount', 'N/A')}")
            print(f"   - 처리 시간: {response_data.get('processingTimeMs', 'N/A')}ms")
            
            # 매칭된 요양보호사 정보
            matched_caregivers = response_data.get('matchedCaregivers', [])
            if matched_caregivers:
                print(f"\n👥 매칭된 요양보호사 목록:")
                for i, caregiver in enumerate(matched_caregivers, 1):
                    caregiver_id = caregiver.get('caregiverId', 'N/A')
                    if len(caregiver_id) > 8:
                        caregiver_id = caregiver_id[:8] + "..."
                    print(f"   {i}. {caregiver.get('name', 'N/A')} (ID: {caregiver_id})")
                    print(f"      - 거리: {caregiver.get('distanceKm', 'N/A')}km")
                    print(f"      - 예상 이동 시간: {caregiver.get('estimatedTravelTime', 'N/A')}분")
                    print(f"      - 주소: {caregiver.get('address', 'N/A')}")
            else:
                print("   매칭된 요양보호사가 없습니다.")
                
            return True
                
        else:
            print(f"❌ 요청 실패! 상태 코드: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 오류 정보:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(f"📋 오류 응답: {response.text}")
            return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 홈케어 매칭 API HTTP 요청 테스트 시작")
    print(f"📍 API 엔드포인트: {API_ENDPOINT}")
    print(f"⏰ 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 API 서버가 실행 중인지 확인하세요:")
    print("   uvicorn app.main:app --host 0.0.0.0 --port 8000")
    
    # 각 테스트 케이스 실행
    test_cases = [
        ("기본 매칭 요청", TEST_DATA.get("basic_request")),
        ("오전 서비스 요청", TEST_DATA.get("morning_service_request")),
        ("오후 서비스 요청", TEST_DATA.get("afternoon_service_request")),
        ("종일 서비스 요청", TEST_DATA.get("full_day_service_request")),
        ("주말 서비스 요청", TEST_DATA.get("weekend_service_request"))
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for test_name, request_data in test_cases:
        if request_data:
            success = test_api_request(test_name, request_data)
            if success:
                success_count += 1
            # API 호출 간 간격
            time.sleep(1)
        else:
            print(f"⚠️ {test_name} 데이터를 찾을 수 없습니다.")
    
    print(f"\n{'='*60}")
    print("📊 테스트 결과 요약")
    print(f"{'='*60}")
    print(f"   - 총 테스트: {total_count}개")
    print(f"   - 성공: {success_count}개")
    print(f"   - 실패: {total_count - success_count}개")
    print(f"   - 성공률: {(success_count/total_count*100):.1f}%")
    print(f"⏰ 테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()