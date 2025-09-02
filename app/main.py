from fastapi import FastAPI
import logging
import os
from dotenv import load_dotenv
from .api.matching import router
from .api.converting import router as converting_router

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Homecare Matching API", 
    version="1.0.0",
    description="요양보호사 매칭 서비스"
)

app.include_router(router, prefix="/matching", tags=["matching"])
app.include_router(converting_router, prefix="/converting", tags=["converting"])

@app.get("/health-check")
def health():
    """헬스체크 엔드포인트"""
    return {
        "status": "ok",
        "message": "Homecare Matching API is running",
        "services": {
            "fastapi": "running"
        }
    }

@app.get("/")
def root():
    """루트 엔드포인트"""
    return {
        "name": "Homecare Matching API",
        "version": "1.0.0",
        "description": "거리 기반 요양보호사 매칭 서비스",
        "endpoints": {
            "rest_api": {
                "matching": "/matching/recommend",
                "converting": "/converting/convert",
                "health": "/health-check"
            }
        }
    }