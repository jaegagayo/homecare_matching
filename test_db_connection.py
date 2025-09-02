#!/usr/bin/env python3
"""
데이터베이스 연결 및 ORM 모델 테스트 스크립트
Docker Compose 환경에서 데이터베이스 연결을 확인합니다.
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import get_db_session, engine
from app.repositories.caregiver_repository import get_all_caregivers
from sqlalchemy import text

async def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("=" * 60)
    print("데이터베이스 연결 테스트 시작")
    print("=" * 60)
    
    try:
        # 1. 데이터베이스 연결 확인
        print("\n1. 데이터베이스 연결 확인")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL 연결 성공")
            print(f"   버전: {version}")
        
        # 2. 테이블 존재 여부 확인
        print("\n2. 테이블 존재 여부 확인")
        async with engine.begin() as conn:
            # 요양보호사 테이블 확인
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%caregiver%'
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"✅ 요양보호사 관련 테이블 발견:")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("⚠️  요양보호사 관련 테이블을 찾을 수 없습니다")
        
        # 3. ORM을 통한 요양보호사 데이터 조회 테스트
        print("\n3. ORM을 통한 데이터 조회 테스트")
        async for session in get_db_session():
            try:
                caregivers = await get_all_caregivers(session)
                print(f"✅ ORM을 통한 데이터 조회 성공")
                print(f"   조회된 요양보호사 수: {len(caregivers)}명")
                
                if caregivers:
                    # 첫 번째 요양보호사 정보 출력 (샘플)
                    first_caregiver = caregivers[0]
                    print(f"   샘플 데이터:")
                    print(f"   - ID: {first_caregiver.caregiverId}")
                    print(f"   - 사용자 ID: {first_caregiver.userId}")
                    print(f"   - 이름: {first_caregiver.name}")
                    print(f"   - 주소: {first_caregiver.address}")
                    print(f"   - 위치: {first_caregiver.location}")
                else:
                    print("   데이터베이스에 요양보호사 데이터가 없습니다")
                    
            except Exception as e:
                print(f"❌ ORM 데이터 조회 실패: {str(e)}")
            finally:
                await session.close()
                
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("데이터베이스 연결 테스트 완료")
    print("=" * 60)
    return True

async def test_matching_api_requirements():
    """매칭 API 요구사항 확인"""
    print("\n" + "=" * 60)
    print("매칭 API 요구사항 검증")
    print("=" * 60)
    
    # 환경 변수 확인
    print("\n1. 환경 변수 확인")
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print(f"✅ DATABASE_URL 설정됨: {database_url}")
    else:
        print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다")
    
    # 필수 모듈 import 확인
    print("\n2. 필수 모듈 import 확인")
    try:
        from app.dto.matching import ServiceRequestDTO, MatchingResponseDTO, MatchedCaregiverDTO
        print("✅ 매칭 DTO 모듈 import 성공")
        
        from app.api.matching import recommend_matching
        print("✅ 매칭 API 엔드포인트 import 성공")
        
    except ImportError as e:
        print(f"❌ 모듈 import 실패: {str(e)}")

async def main():
    """메인 테스트 함수"""
    print("홈케어 매칭 시스템 데이터베이스 연결 테스트")
    print("Docker Compose 환경에서 실행해주세요:")
    print("cd /Users/jaehun/gh/jaegagayo/homecare_infra/code")
    print("docker compose up -d postgres")
    print("\n")
    
    # 데이터베이스 연결 테스트
    success = await test_database_connection()
    
    # 매칭 API 요구사항 확인
    await test_matching_api_requirements()
    
    if success:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("이제 매칭 API를 테스트할 수 있습니다.")
    else:
        print("\n💡 Docker Compose로 PostgreSQL을 먼저 실행해주세요:")
        print("   cd /Users/jaehun/gh/jaegagayo/homecare_infra/code")
        print("   docker compose up -d postgres")

if __name__ == "__main__":
    asyncio.run(main())