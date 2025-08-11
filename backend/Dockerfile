# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/data/contacts.db \
    HOST=0.0.0.0 \
    PORT=5000 \
    ALLOWED_ORIGIN=* \
    MAX_BODY_BYTES=65536 \
    REQUESTS_PER_MINUTE=120

# Create non-root user
RUN useradd -u 10001 -m appuser

WORKDIR /app

# Copy backend server
COPY app.py /app/app.py

# Data directory for SQLite
RUN mkdir -p /data && chown -R appuser:appuser /data

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD python - <<'PY'
import urllib.request
import sys
try:
    with urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
PY

CMD ["python", "app.py"]