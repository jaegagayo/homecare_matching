#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새로운 위치 정보 형식 사용 예시

요청하신 형식:
{
    "roadAddress": String,
    "jibunAddress": String,
    "addressElements": Object[],
    "x": Integer,
    "y": Integer
}
"""

from app.dto.matching import LocationInfo, ServiceRequestDTO, CaregiverForMatchingDTO, MatchingRequestDTO
from app.models.matching import LocationInfo as ModelLocationInfo

def create_example_location_info():
    """새로운 위치 정보 형식으로 예시 데이터 생성"""
    
    # 서울시 강남구 테헤란로 123 예시
    seoul_location = LocationInfo(
        roadAddress="서울특별시 강남구 테헤란로 123",
        jibunAddress="서울특별시 강남구 역삼동 123-45",
        addressElements=[
            {"type": "sido", "name": "서울특별시"},
            {"type": "sigungu", "name": "강남구"},
            {"type": "dong", "name": "역삼동"},
            {"type": "road", "name": "테헤란로"},
            {"type": "buildingNumber", "name": "123"}
        ],
        x=127028,  # 경도 (정수)
        y=37356    # 위도 (정수)
    )
    
    return seoul_location

def create_example_service_request():
    """새로운 위치 정보를 사용한 서비스 요청 예시"""
    
    location = create_example_location_info()
    
    service_request = ServiceRequestDTO(
        serviceRequestId="SR001",
        consumerId="CONSUMER001",
        serviceAddress="서울특별시 강남구 테헤란로 123",
        addressType="ROAD",
        location=location,
        preferredTime="09:00-18:00",
        duration="8시간",
        serviceType="방문요양",
        requestStatus="PENDING",
        requestDate="2024-01-15",
        additionalInformation="거동이 불편한 노인 환자"
    )
    
    return service_request

def create_example_caregiver():
    """새로운 위치 정보를 사용한 요양보호사 예시"""
    
    # 서울시 서초구 서초대로 456 예시
    caregiver_location = LocationInfo(
        roadAddress="서울특별시 서초구 서초대로 456",
        jibunAddress="서울특별시 서초구 서초동 456-78",
        addressElements=[
            {"type": "sido", "name": "서울특별시"},
            {"type": "sigungu", "name": "서초구"},
            {"type": "dong", "name": "서초동"},
            {"type": "road", "name": "서초대로"},
            {"type": "buildingNumber", "name": "456"}
        ],
        x=127008,  # 경도 (정수)
        y=37340    # 위도 (정수)
    )
    
    caregiver = CaregiverForMatchingDTO(
        caregiverId="CG001",
        userId="USER001",
        availableTimes="09:00-18:00",
        address="서울특별시 서초구 서초대로 456",
        serviceType="방문요양",
        daysOff="토,일",
        career="5년",
        koreanProficiency="모국어",
        isAccompanyOuting=True,
        selfIntroduction="경험 많은 요양보호사입니다",
        isVerified=True,
        baseLocation=caregiver_location,
        careerYears=5,
        workDays="월,화,수,목,금",
        workArea="서울시 강남구, 서초구",
        transportation="자차",
        supportedConditions="치매, 거동불편, 중증환자"
    )
    
    return caregiver

def demonstrate_coordinate_conversion():
    """좌표 변환 예시"""
    
    location = create_example_location_info()
    
    print("=== 새로운 위치 정보 형식 ===")
    print(f"도로명 주소: {location.roadAddress}")
    print(f"지번 주소: {location.jibunAddress}")
    print(f"경도 (x): {location.x}")
    print(f"위도 (y): {location.y}")
    
    print("\n=== 기존 코드 호환성 ===")
    coordinates = location.get_coordinates()
    print(f"get_coordinates() 결과: {coordinates}")
    print(f"위도: {coordinates[0]}, 경도: {coordinates[1]}")
    
    print("\n=== 주소 구성 요소 ===")
    for element in location.addressElements:
        print(f"- {element['type']}: {element['name']}")

def demonstrate_matching_request():
    """매칭 요청 예시"""
    
    service_request = create_example_service_request()
    caregiver = create_example_caregiver()
    
    matching_request = MatchingRequestDTO(
        serviceRequest=service_request,
        candidateCaregivers=[caregiver]
    )
    
    print("\n=== 매칭 요청 구조 ===")
    print(f"서비스 요청 ID: {matching_request.serviceRequest.serviceRequestId}")
    print(f"서비스 위치: {matching_request.serviceRequest.location.roadAddress}")
    print(f"요양보호사 위치: {matching_request.candidateCaregivers[0].baseLocation.roadAddress}")
    
    # 거리 계산을 위한 좌표 추출
    service_coords = matching_request.serviceRequest.location.get_coordinates()
    caregiver_coords = matching_request.candidateCaregivers[0].baseLocation.get_coordinates()
    
    print(f"서비스 좌표: {service_coords}")
    print(f"요양보호사 좌표: {caregiver_coords}")

if __name__ == "__main__":
    print("🏠 홈케어 매칭 시스템 - 새로운 위치 정보 형식 예시")
    print("=" * 60)
    
    demonstrate_coordinate_conversion()
    demonstrate_matching_request()
    
    print("\n" + "=" * 60)
    print("✅ 모든 예시가 성공적으로 실행되었습니다!")
