FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/app/src \
    ARTIFACTS_ROOT=/data/artifacts

WORKDIR /app

# System fonts required by the chart-rendering pipeline (Pillow/PIL)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fonts-dejavu-core \
        libfreetype6 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/data/artifacts"]

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "profile_backend.interfaces.http.api:app", "--host", "0.0.0.0", "--port", "8000"]
