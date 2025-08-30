from fastapi import FastAPI
import logging
import asyncio
from contextlib import asynccontextmanager
from .api.matching import router
from .api.converting import router as converting_router
from .grpc_service import serve_grpc

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
    logger.info("통합 서버 시작: FastAPI + gRPC")
    grpc_task = asyncio.create_task(serve_grpc(50051))
    
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
app.include_router(converting_router, prefix="/converting", tags=["converting"])

@app.get("/health-check")
def health():
    """헬스체크 엔드포인트"""
    return {
        "status": "ok", 
        "message": "Homecare Matching API is running",
        "services": {
            "fastapi": "running",
            "grpc": "running on port 50051"
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
            },
            "grpc": {
                "port": 50051,
                "service": "matching.MatchingService",
                "methods": [
                    "GetMatchingRecommendations",
                    "HealthCheck"
                ]
            }
        }
    }