# 파이썬 이미지 사용 # slim 이미지는 불필요한 패키지가 없어 더 가볍지만,
# 개발 단계에서 필요한 패키지가 없을 수 있어 기본 이미지를 사용
FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /code

# requirements.txt 복사 및 의존성 설치
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
# 애플리케이션 코드 복사
COPY ./app /code/app

# 서버 실행 - uvicorn으로 직접 실행 (환경 변수 사용, 기본값 설정)
CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${FASTAPI_PORT:-8000} --log-level ${LOG_LEVEL:-info} --reload"]