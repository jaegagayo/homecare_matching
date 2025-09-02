#!/usr/bin/env python3
"""
LLM 선호조건 필터링 통합 테스트
"""

import asyncio
import sys
import os
sys.path.append('.')

from app.api.converting import convert_non_structured_data_to_structured_data
from app.dto.converting import ConvertNonStructuredDataToStructuredDataRequest

async def test_llm_conversion():
    """LLM 변환 기능 테스트"""
    print("🧪 LLM 선호조건 변환 테스트 시작...")
    
    # 테스트 데이터
    test_cases = [
        "월화수 오전 9시부터 오후 6시까지 강남구에서 치매 어르신 방문요양 서비스 가능합니다",
        "주말 포함 24시간 간병 가능하며, 와상환자 전문입니다. 서울 전 지역 이동 가능",
        "평일 오후 2시-6시, 여성 어르신만 가능, 대중교통 이용"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        try:
            print(f"\n📝 테스트 케이스 {i}: {test_text[:50]}...")
            
            request = ConvertNonStructuredDataToStructuredDataRequest(
                non_structured_data=test_text
            )
            
            # OpenRouter API 키가 없으면 스킵
            if not os.getenv("OPENROUTER_API_KEY"):
                print("⚠️  OPENROUTER_API_KEY 환경변수가 설정되지 않음 - 실제 API 호출 스킵")
                continue
                
            result = await convert_non_structured_data_to_structured_data(request)
            print(f"✅ 변환 결과:")
            print(f"   - 근무 요일: {result.day_of_week}")
            print(f"   - 근무 시간: {result.work_start_time} ~ {result.work_end_time}")
            print(f"   - 근무 지역: {result.work_area}")
            print(f"   - 서비스 유형: {result.service_types}")
            print(f"   - 지원 질환: {result.supported_conditions}")
            
        except Exception as e:
            print(f"❌ 테스트 케이스 {i} 실패: {str(e)}")

def test_import():
    """모듈 import 테스트"""
    print("🔍 모듈 import 테스트...")
    try:
        from app.api.matching import filter_by_preferences, evaluate_caregiver_match
        from app.models.matching import CaregiverForMatching, LocationInfo
        print("✅ 모든 모듈 import 성공")
        return True
    except Exception as e:
        print(f"❌ 모듈 import 실패: {str(e)}")
        return False

async def main():
    """메인 테스트 함수"""
    print("🚀 LLM 매칭 시스템 통합 테스트")
    print("=" * 50)
    
    # 1. Import 테스트
    if not test_import():
        return
    
    # 2. LLM 변환 테스트
    await test_llm_conversion()
    
    print("\n" + "=" * 50)
    print("🎯 테스트 완료")
    
    # API 키 설정 안내
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\n💡 실제 LLM 테스트를 위해서는:")
        print("   1. .env 파일에 OPENROUTER_API_KEY 설정")
        print("   2. python test_llm_matching.py 재실행")

if __name__ == "__main__":
    asyncio.run(main())