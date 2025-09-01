# 파이썬 이미지 사용
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /code

# requirements.txt 복사 및 의존성 설치
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install --no-cache-dir grpcio grpcio-tools

# proto 파일 복사
COPY ./proto /code/proto

# gRPC 코드 생성 디렉토리 생성
RUN mkdir -p /code/app/grpc_generated

# proto 파일을 Python 코드로 컴파일
# -I 옵션: proto 파일의 위치를 지정
# --python_out, --grpc_python_out: 생성된 .py 파일이 저장될 위치를 지정
RUN python -m grpc_tools.protoc \
    -I/code/proto \
    --python_out=/code/app/grpc_generated \
    --grpc_python_out=/code/app/grpc_generated \
    /code/proto/matching_service.proto

# 나머지 애플리케이션 코드 복사
COPY ./app /code/app
COPY ./run_server.py /code/run_server.py

# 생성된 gRPC 코드를 찾을 수 있도록 PYTHONPATH에 경로 추가
ENV PYTHONPATH=/code/app/grpc_generated:${PYTHONPATH}

# 서버 실행
CMD ["python", "run_server.py"]