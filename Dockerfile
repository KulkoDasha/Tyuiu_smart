# Dockerfile для Telegram-бота «ТИУмничка»
# Stack: Python 3.10 + Go binary (Yandex Integration) + PostgreSQL

FROM python:3.10-slim AS base

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Установка рабочей директории
WORKDIR /app

# Создание пользователя для запуска приложения (без root)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /app/upload_script && \
    chown -R appuser:appuser /app

# Переключение на не-root пользователя
USER appuser

# === копируем requirements.txt ПЕРЕД pip install ===
COPY --chown=appuser:appuser requirements.txt .

# Установка Python-пакетов с зеркалом для РФ и увеличенными таймаутами
RUN pip install --no-cache-dir --user -r requirements.txt \
        --index-url https://pypi.org/simple \
        --retries=20 \
        --trusted-host pypi.org

# === Application image ===
FROM base AS application

# Копирование исходного кода приложения
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser database/ ./database/
COPY --chown=appuser:appuser alembic.ini .

# Копирование entrypoint-скрипта
COPY --chown=appuser:appuser entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Копирование Go-бинарника и его .env (только для чтения)
COPY --chown=appuser:appuser upload_script/ ./upload_script/
RUN chmod +x /app/upload_script/binary

# Создание директории для логов (если не смонтирована volume)
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_PATH=/app/logs \
    YANDEX_BINARY_PATH=/app/upload_script/binary

# Healthcheck для контейнера бота (проверка, что процесс запущен)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Точка входа и команда запуска
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "app/main.py"]