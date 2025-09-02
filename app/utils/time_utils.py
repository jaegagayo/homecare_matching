"""
시간 관련 유틸리티 함수 모듈
선호시간대 비교 및 시간대 겹침 확인 기능 제공
"""

import re
from datetime import time
from typing import Optional, Tuple, List
import logging

# DTO import 추가
from ..dto.matching import CaregiverForMatchingDTO

logger = logging.getLogger(__name__)

def parse_time(time_str: str) -> Optional[time]:
    """
    시간 문자열(HH:MM 형식)을 datetime.time 객체로 파싱
    
    Args:
        time_str: "HH:MM" 형식의 시간 문자열
        
    Returns:
        datetime.time 객체 또는 파싱 실패 시 None
    """
    if not time_str:
        return None
        
    try:
        # 다양한 시간 형식 지원
        time_pattern = r'(\d{1,2}):(\d{2})'
        match = re.match(time_pattern, time_str.strip())
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            # 시간 유효성 검증
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute)
            else:
                logger.warning(f"유효하지 않은 시간: {time_str}")
                return None
        else:
            logger.warning(f"시간 형식 파싱 실패: {time_str}")
            return None
            
    except (ValueError, AttributeError) as e:
        logger.error(f"시간 파싱 중 오류: {time_str}, {e}")
        return None

def is_time_overlap(
    start_time1: Optional[str], 
    end_time1: Optional[str],
    start_time2: Optional[str], 
    end_time2: Optional[str]
) -> bool:
    """
    두 시간대가 겹치는지 확인
    
    Args:
        - 선호 시간
        start_time1: 첫 번째 시간대 시작 시간 (HH:MM)
        end_time1: 첫 번째 시간대 종료 시간 (HH:MM)
        - 요양보호사 근무 시간
        start_time2: 두 번째 시간대 시작 시간 (HH:MM)
        end_time2: 두 번째 시간대 종료 시간 (HH:MM)
        
    Returns:
        bool: 시간대가 겹치면 True, 아니면 False
    """
    # 필수 시간 정보가 없는 경우 기본적으로 겹친다고 판단 (안전 장치)
    if not all([start_time1, end_time1, start_time2, end_time2]):
        logger.debug("필수 시간 정보가 부족하여 기본적으로 겹침 처리")
        return True
        
    # 시간 문자열 파싱
    start1 = parse_time(start_time1)
    end1 = parse_time(end_time1)
    start2 = parse_time(start_time2)
    end2 = parse_time(end_time2)
    
    # 파싱 실패 시 기본적으로 겹친다고 판단
    if not all([start1, end1, start2, end2]):
        logger.warning("시간 파싱 실패로 기본적으로 겹침 처리")
        return True
    
    # 시간대 겹침 확인 로직
    return start2 <= start1 and end2 >= end1

def filter_caregivers_by_time_preference(
    caregivers: List[CaregiverForMatchingDTO],
    preferred_start_time: Optional[str],
    preferred_end_time: Optional[str]
) -> List[CaregiverForMatchingDTO]:
    """
    요양보호사 목록에서 선호시간대와 겹치는 사람들만 필터링
    
    Args:
        caregivers: 요양보호사 DTO 목록
        preferred_start_time: 신청자 선호 시작 시간 (HH:MM)
        preferred_end_time: 신청자 선호 종료 시간 (HH:MM)
        
    Returns:
        List[CaregiverForMatchingDTO]: 시간대가 겹치는 요양보호사 목록
    """
    if not preferred_start_time or not preferred_end_time:
        logger.info("신청자 선호시간대 정보가 없어 모든 요양보호사 통과")
        return caregivers
        
    filtered_caregivers = []
    
    for caregiver in caregivers:
        caregiver_start_time = getattr(caregiver, 'workStartTime', None)
        caregiver_end_time = getattr(caregiver, 'workEndTime', None)
        
        # 요양보호사 근무시간 정보가 없는 경우 기본적으로 통과
        if not caregiver_start_time or not caregiver_end_time:
            logger.debug(f"요양보호사 {caregiver.caregiverId} 근무시간 정보 없음 - 통과")
            filtered_caregivers.append(caregiver)
            continue
            
        # 시간대 겹침 확인
        if is_time_overlap(
            preferred_start_time, preferred_end_time,
            caregiver_start_time, caregiver_end_time
        ):
            filtered_caregivers.append(caregiver)
            logger.debug(f"요양보호사 {caregiver.caregiverId} 시간대 겹침 - 통과")
        else:
            logger.debug(f"요양보호사 {caregiver.caregiverId} 시간대 불일치 - 제외")
            
    logger.info(f"시간대 필터링 완료: 전체 {len(caregivers)}명 중 {len(filtered_caregivers)}명 통과")
    return filtered_caregivers

def validate_time_range(start_time: str, end_time: str) -> bool:
    """
    시간 범위 유효성 검증 (시작 시간이 종료 시간보다 이른지 확인)
    
    Args:
        start_time: 시작 시간 (HH:MM)
        end_time: 종료 시간 (HH:MM)
        
    Returns:
        bool: 유효한 시간 범위이면 True, 아니면 False
    """
    start = parse_time(start_time)
    end = parse_time(end_time)
    
    if not start or not end:
        return False
        
    return start < end

# 테스트용 함수
def test_time_utils():
    """시간 유틸리티 함수 테스트"""
    print("시간 유틸리티 테스트 시작")
    
    # 시간 파싱 테스트
    test_times = ["09:00", "13:30", "18:45", "24:00", "abc"]
    for t in test_times:
        result = parse_time(t)
        print(f"파싱 '{t}': {result}")
    
    # 시간대 겹침 테스트
    test_cases = [
        # (start1, end1, start2, end2, expected)
        ("09:00", "18:00", "10:00", "17:00", True),  # 완전 포함
        ("10:00", "17:00", "09:00", "18:00", True),  # 완전 포함 (반대)
        ("09:00", "12:00", "11:00", "14:00", True),  # 부분 겹침
        ("09:00", "10:00", "11:00", "12:00", False), # 겹치지 않음
        ("14:00", "18:00", "09:00", "12:00", False), # 겹치지 않음
    ]
    
    for start1, end1, start2, end2, expected in test_cases:
        result = is_time_overlap(start1, end1, start2, end2)
        status = "✓" if result == expected else "✗"
        print(f"{status} {start1}-{end1} vs {start2}-{end2}: {result} (기대: {expected})")

if __name__ == "__main__":
    test_time_utils()