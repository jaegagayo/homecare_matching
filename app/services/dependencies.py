"""
서비스 의존성 주입 설정
FastAPI Depends 패턴을 활용한 서비스 레이어 주입
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .data_service import MatchingDataService
from .model_converter import ModelConverter
from ..database.connection import get_db

def get_matching_data_service(
    db: AsyncSession = Depends(get_db)
) -> MatchingDataService:
    """
    MatchingDataService 의존성 주입
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        MatchingDataService: 매칭 데이터 서비스 인스턴스
    """
    return MatchingDataService(db)