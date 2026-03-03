FROM python:3.10-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc postgresql-client curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

WORKDIR /app

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /app/uploader_script && \
    chown -R appuser:appuser /app

USER appuser

COPY --chown=appuser:appuser requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt \
    --index-url https://pypi.org/simple \
    --default-timeout=300 --retries=20 --trusted-host pypi.org

FROM base AS application

COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser database/ ./database/
COPY --chown=appuser:appuser alembic.ini .

COPY --chown=appuser:appuser entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY --chown=appuser:appuser uploader_script/ ./uploader_script/
RUN chmod +x /app/uploader_script/binary

RUN mkdir -p /app/logs && chmod 755 /app/logs

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_PATH=/app/logs \
    YANDEX_BINARY_PATH=/app/uploader_script/binary

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep -f "python.*main.py" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "app/main.py"]