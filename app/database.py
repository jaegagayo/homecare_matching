"""
데이터베이스 설정 및 세션 관리 모듈
SQLAlchemy를 사용한 읽기 전용 데이터베이스 연결 설정
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 URL (Spring Boot에서 초기화된 DB)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/homecare_db"
)

# 읽기 전용 비동기 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 개발 환경에서 SQL 쿼리 로깅
    poolclass=NullPool,
    future=True
)

# 비동기 세션 팩토리 (읽기 전용)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# 베이스 모델
Base = declarative_base()

async def get_db_session() -> AsyncSession:
    """
    읽기 전용 비동기 데이터베이스 세션을 제공하는 의존성 함수
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()