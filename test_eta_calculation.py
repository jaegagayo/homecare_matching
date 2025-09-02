"""
ETA 계산 로직 테스트 스크립트

목 데이터를 사용하여 새로운 네이버 Direction API 클라이언트를 테스트합니다.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.utils.naver_direction import ETACalculator
from app.models.matching import LocationInfo

async def test_eta_calculation():
    """ETA 계산 테스트"""
    
    print("🚀 ETA 계산 테스트 시작")
    print("=" * 50)
    
    # 목 데이터 사용 ETACalculator 초기화
    eta_calculator = ETACalculator(
        use_mock_data=True, 
        mock_data_path="tests/mock_data/naver_map_api_dataset.json"
    )
    
    # 테스트 위치 데이터 (목 데이터에 존재하는 좌표)
    test_locations = [
        {
            "name": "서울시청",
            "location": LocationInfo(
                roadAddress="서울특별시 중구 세종대로 110",
                jibunAddress="서울특별시 중구 태평로1가 31",
                addressElements=[],
                x=126.978652,
                y=37.566826
            )
        },
        {
            "name": "네이버 그린팩토리",
            "location": LocationInfo(
                roadAddress="경기도 성남시 분당구 불정로 6",
                jibunAddress="경기도 성남시 분당구 정자동 178-1",
                addressElements=[],
                x=127.1052133,
                y=37.3595122
            )
        },
        {
            "name": "임의 위치 (부산)",
            "location": LocationInfo(
                roadAddress="부산광역시 해운대구",
                jibunAddress="부산광역시 해운대구",
                addressElements=[],
                x=129.075986,
                y=35.179470
            )
        }
    ]
    
    print("📍 테스트 위치:")
    for i, loc_data in enumerate(test_locations, 1):
        location = loc_data["location"]
        print(f"  {i}. {loc_data['name']}: ({location.y}, {location.x})")
    
    print("\n🔍 ETA 계산 테스트:")
    print("-" * 30)
    
    # 1. 개별 ETA 계산 테스트
    print("\n1️⃣ 개별 ETA 계산:")
    origin = test_locations[0]["location"]  # 서울시청
    destination = test_locations[1]["location"]  # 네이버 그린팩토리
    
    eta_minutes = await eta_calculator.calculate_eta(origin, destination)
    print(f"   서울시청 → 네이버 그린팩토리: {eta_minutes}분")
    
    # 2. 목 데이터에 없는 경로 (Fallback 테스트)
    origin = test_locations[0]["location"]  # 서울시청
    destination = LocationInfo(
        roadAddress="제주시",
        jibunAddress="제주시",
        addressElements=[],
        x=126.5219,
        y=33.4996
    )
    
    eta_minutes = await eta_calculator.calculate_eta(origin, destination)
    print(f"   서울시청 → 제주시 (Fallback): {eta_minutes}분")
    
    # 3. 배치 ETA 계산 테스트
    print("\n2️⃣ 배치 ETA 계산:")
    origins = [loc_data["location"] for loc_data in test_locations]
    destination = test_locations[1]["location"]  # 네이버 그린팩토리
    
    eta_results = await eta_calculator.batch_calculate_eta(origins, destination)
    
    for i, (loc_data, eta) in enumerate(zip(test_locations, eta_results)):
        print(f"   {loc_data['name']} → 네이버 그린팩토리: {eta}분")
    
    print("\n✅ ETA 계산 테스트 완료!")
    print("=" * 50)

async def test_real_api():
    """실제 API 테스트 (환경변수가 설정된 경우)"""
    
    print("\n🌐 실제 네이버 API 테스트")
    print("=" * 50)
    
    try:
        # 실제 API 사용 ETACalculator 초기화
        eta_calculator = ETACalculator(use_mock_data=False)
        
        # 테스트 위치
        origin = LocationInfo(
            roadAddress="서울특별시 중구 세종대로 110",
            jibunAddress="서울특별시 중구 태평로1가 31", 
            addressElements=[],
            x=126.978652,
            y=37.566826
        )
        
        destination = LocationInfo(
            roadAddress="경기도 성남시 분당구 불정로 6",
            jibunAddress="경기도 성남시 분당구 정자동 178-1",
            addressElements=[],
            x=127.1052133,
            y=37.3595122
        )
        
        print("📍 실제 API 호출:")
        print(f"   출발지: 서울시청 ({origin.y}, {origin.x})")
        print(f"   목적지: 네이버 그린팩토리 ({destination.y}, {destination.x})")
        
        eta_minutes = await eta_calculator.calculate_eta(origin, destination)
        print(f"   실제 API ETA: {eta_minutes}분")
        
        print("\n✅ 실제 API 테스트 완료!")
        
    except ValueError as e:
        print(f"⚠️  환경변수 미설정: {str(e)}")
        print("   실제 API 테스트를 건너뜁니다.")
    except Exception as e:
        print(f"❌ 실제 API 테스트 실패: {str(e)}")
    
    print("=" * 50)

async def main():
    """메인 테스트 함수"""
    
    print("🧪 네이버 Direction ETA 계산 시스템 테스트")
    print("=" * 60)
    
    # 1. 목 데이터를 사용한 테스트
    await test_eta_calculation()
    
    # 2. 실제 API 테스트 (선택적)
    await test_real_api()
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())