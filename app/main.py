from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from .api.matching import router
from .database.connection import init_db, close_db

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작 시
    logger.info("애플리케이션 시작 - 데이터베이스 연결 초기화")
    try:
        await init_db()
        logger.info("데이터베이스 연결 완료")
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        # 실제 운영에서는 애플리케이션을 종료하거나 다른 처리 필요
    
    yield
    
    # 애플리케이션 종료 시
    logger.info("애플리케이션 종료 - 데이터베이스 연결 해제")
    try:
        await close_db()
        logger.info("데이터베이스 연결 해제 완료")
    except Exception as e:
        logger.error(f"데이터베이스 연결 해제 실패: {e}")

app = FastAPI(
    title="Homecare Matching API", 
    version="1.0.0",
    lifespan=lifespan
)
app.include_router(router, prefix="/matching", tags=["matching"])

@app.get("/health-check")
def health():
    return {"status": "ok"}