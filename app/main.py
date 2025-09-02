from fastapi import FastAPI
import logging
import asyncio
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from .api.matching import router
from .grpc_service import serve_grpc

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# gRPC 서버 태스크를 저장할 변수
grpc_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 앱 시작/종료 시 gRPC 서버도 함께 관리"""
    global grpc_task
    
    # 시작 시 gRPC 서버 실행
    grpc_port = int(os.getenv("GRPC_PORT", 50051))
    logger.info("통합 서버 시작: FastAPI + gRPC")
    grpc_task = asyncio.create_task(serve_grpc(grpc_port))
    
    yield
    
    # 종료 시 gRPC 서버 정리
    if grpc_task:
        logger.info("gRPC 서버 종료 중...")
        grpc_task.cancel()
        try:
            await grpc_task
        except asyncio.CancelledError:
            logger.info("gRPC 서버 종료 완료")

app = FastAPI(
    title="Homecare Matching API", 
    version="1.0.0",
    description="거리 기반 요양보호사 매칭 서비스 (FastAPI + gRPC)",
    lifespan=lifespan
)

app.include_router(router, prefix="/matching", tags=["matching"])

@app.get("/health-check")
def health():
    """헬스체크 엔드포인트"""
    grpc_port = int(os.getenv("GRPC_PORT", 50051))
    return {
        "status": "ok", 
        "message": "Homecare Matching API is running",
        "services": {
            "fastapi": "running",
            "grpc": f"running on port {grpc_port}"
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
                "health": "/health-check"
            },
            "grpc": {
                "port": int(os.getenv("GRPC_PORT", 50051)),
                "service": "matching.MatchingService",
                "methods": [
                    "GetMatchingRecommendations",
                    "HealthCheck"
                ]
            }
        }
    }