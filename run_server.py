#!/usr/bin/env python3
"""
통합 서버 실행 스크립트
FastAPI (REST API) + gRPC 서버를 동시에 실행
"""

import uvicorn
import logging

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 홈케어 매칭 통합 서버 시작")
    logger.info("📡 FastAPI (REST API): http://localhost:8000")
    logger.info("🔗 gRPC 서버: localhost:50051")
    logger.info("📋 API 문서: http://localhost:8000/docs")
    
    # FastAPI 서버 실행 (gRPC는 lifespan에서 자동 시작)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )