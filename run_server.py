#!/usr/bin/env python3
"""
통합 서버 실행 스크립트
FastAPI (REST API) + gRPC 서버를 동시에 실행
"""

import uvicorn
import logging
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    # .env 파일 로드
    load_dotenv()
    
    # 환경변수에서 설정값 가져오기
    host = os.getenv("HOST", "0.0.0.0")
    fastapi_port = int(os.getenv("FASTAPI_PORT", 8000))
    grpc_port = int(os.getenv("GRPC_PORT", 50051))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 홈케어 매칭 통합 서버 시작")
    logger.info(f"📡 FastAPI (REST API): http://localhost:{fastapi_port}")
    logger.info(f"🔗 gRPC 서버: localhost:{grpc_port}")
    logger.info(f"📋 API 문서: http://localhost:{fastapi_port}/docs")
    
    # FastAPI 서버 실행 (gRPC는 lifespan에서 자동 시작)
    uvicorn.run(
        "app.main:app",
        host=host,
        port=fastapi_port,
        reload=True,
        log_level=log_level
    )