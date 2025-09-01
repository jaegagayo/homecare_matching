# 
FROM python:3.10

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./app /code/app
COPY ./run_server.py /code/run_server.py

# FastAPI + gRPC 통합 서버 실행
CMD ["python", "run_server.py"]