FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY content /app/content
COPY scripts /app/scripts
COPY start.sh /app/start.sh

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["sh", "-c", "if [ ! -f /app/db/progress.sqlite ]; then python3 scripts/build_and_verify.py || true; fi && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
