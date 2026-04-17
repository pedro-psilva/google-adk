FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/app/backend/src

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY profile_report_automation ./profile_report_automation
COPY skills/profile-report-automation/scripts ./skills/profile-report-automation/scripts

RUN mkdir -p /app/artifacts /app/backend/var

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "profile_backend.interfaces.http.api:app", "--host", "0.0.0.0", "--port", "8000"]
