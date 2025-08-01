"""
데이터베이스 연결 설정
SQLAlchemy + asyncpg를 사용한 PostgreSQL 연결
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from databases import Database
import logging

logger = logging.getLogger(__name__)

# 환경 변수에서 데이터베이스 URL 가져오기
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://homecare_user:homecare_password@postgres:5432/homecare_db"  # Docker Compose 설정과 일치
)

# SQLAlchemy 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 개발 중에는 쿼리 로그 출력
    pool_size=20,
    max_overflow=0,
)

# 세션 팩토리 생성
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Database 인스턴스 (FastAPI와의 호환성을 위해)
database = Database(DATABASE_URL)

# Base 클래스 정의
class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    """
    비동기 데이터베이스 세션을 반환하는 의존성 함수
    FastAPI의 Depends에서 사용
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """데이터베이스 연결 초기화"""
    try:
        await database.connect()
        logger.info("데이터베이스 연결 성공")
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        raise

async def close_db():
    """데이터베이스 연결 종료"""
    try:
        await database.disconnect()
        logger.info("데이터베이스 연결 종료")
    except Exception as e:
        logger.error(f"데이터베이스 연결 종료 실패: {e}")