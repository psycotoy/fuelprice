# 베이스 이미지 설정
FROM python:3.10-slim

# 작업 디렉터리 설정
WORKDIR /app

# 기본 의존성 설치
RUN apt-get update && \
    apt-get install -y build-essential libproj-dev proj-bin && \
    rm -rf /var/lib/apt/lists/*

# PROJ 라이브러리 경로 설정
ENV PROJ_LIB=/usr/share/proj

# requirements.txt 파일을 컨테이너로 복사하고, 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 파일 복사
COPY . .

# 앱 실행 명령어
CMD ["python", "fuelprice.py"]
