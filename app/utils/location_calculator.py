"""
위치 기반 계산 유틸리티

네이버 지도 API 호출을 최소화하고 순수 수학적 계산으로 
두 지점 간의 거리를 계산하는 모듈입니다.
"""

import math
from typing import List, Tuple
from app.models.matching import LocationInfo, CaregiverForMatching


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    두 지점 간의 직선 거리를 Haversine 공식으로 계산합니다.
    
    Args:
        lat1: 첫 번째 지점의 위도
        lon1: 첫 번째 지점의 경도
        lat2: 두 번째 지점의 위도
        lon2: 두 번째 지점의 경도
    
    Returns:
        float: 두 지점 간의 거리 (km)
    """
    # 지구의 반지름 (km)
    R = 6371.0
    
    # 위도와 경도를 라디안으로 변환
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 위도와 경도 차이
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine 공식
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 거리 계산
    distance = R * c
    
    return round(distance, 2)


def is_within_radius(
    center_location: LocationInfo, 
    target_location: LocationInfo, 
    radius_km: float = 15.0
) -> bool:
    """
    중심 위치에서 반경 내에 대상 위치가 있는지 확인합니다.
    
    Args:
        center_location: 중심 위치 정보
        target_location: 확인할 대상 위치 정보
        radius_km: 반경 (km, 기본값: 15km)
    
    Returns:
        bool: 반경 내에 있으면 True, 아니면 False
    """
    distance = calculate_distance_km(
        center_location.y, center_location.x,
        target_location.y, target_location.x
    )
    
    return distance <= radius_km


def filter_caregivers_by_distance(
    request_location: LocationInfo,
    caregivers: List[CaregiverForMatching],
    radius_km: float = 15.0
) -> List[Tuple[CaregiverForMatching, float]]:
    """
    요청 위치를 기준으로 반경 내 요양보호사들을 필터링합니다.
    
    Args:
        request_location: 서비스 요청 위치
        caregivers: 요양보호사 목록
        radius_km: 반경 (km, 기본값: 15km)
    
    Returns:
        List[Tuple[CaregiverForMatching, float]]: (요양보호사, 거리) 튜플 리스트
        거리 순으로 정렬됨
    """
    filtered_caregivers = []
    
    for caregiver in caregivers:
        distance = calculate_distance_km(
            request_location.y, request_location.x,
            caregiver.base_location.y, caregiver.base_location.x
        )
        
        if distance <= radius_km:
            filtered_caregivers.append((caregiver, distance))
    
    # 거리 순으로 정렬
    filtered_caregivers.sort(key=lambda x: x[1])
    
    return filtered_caregivers


def get_nearby_caregivers_ids(
    request_location: LocationInfo,
    caregivers: List[CaregiverForMatching],
    radius_km: float = 15.0
) -> List[str]:
    """
    반경 내 요양보호사 ID 목록을 거리 순으로 반환합니다.
    
    Args:
        request_location: 서비스 요청 위치
        caregivers: 요양보호사 목록
        radius_km: 반경 (km, 기본값: 15km)
    
    Returns:
        List[str]: 반경 내 요양보호사 ID 목록 (거리 순 정렬)
    """
    filtered_caregivers = filter_caregivers_by_distance(
        request_location, caregivers, radius_km
    )
    
    return [caregiver.caregiver_id for caregiver, _ in filtered_caregivers]


def calculate_estimated_travel_time(distance_km: float) -> int:
    """
    거리를 기반으로 예상 이동 시간을 계산합니다.
    
    Args:
        distance_km: 거리 (km)
    
    Returns:
        int: 예상 이동 시간 (분)
        
    Note:
        - 도심 지역 평균 속도 25km/h 가정
        - 최소 10분, 최대 60분으로 제한
    """
    # 도심 지역 평균 속도 (km/h)
    AVERAGE_SPEED_KMH = 25
    
    # 시간 계산 (분)
    travel_time_minutes = (distance_km / AVERAGE_SPEED_KMH) * 60
    
    # 최소 10분, 최대 60분으로 제한
    travel_time_minutes = max(10, min(60, travel_time_minutes))
    
    return round(travel_time_minutes)