#!/bin/sh
set -e

echo "=== 🚀 Starting Tiumnichka Bot ==="

# Переопределение DB_CREDENTIALS для Docker
if [ -n "$DB_CREDENTIALS_OVERRIDE" ]; then
    export DB_CREDENTIALS="$DB_CREDENTIALS_OVERRIDE"
fi

# Ожидание готовности БД
echo "⏳ Waiting for database..."
until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" 2>/dev/null; do
    sleep 2
done
echo "✅ Database ready"

# === ИНИЦИАЛИЗАЦИЯ БД ===
# Проверяем, нужна ли первичная инициализация
INIT_CHECK=$(python -c "
import asyncio, sys
from database.init_db import is_fresh_database
result = asyncio.run(is_fresh_database())
print('FRESH' if result else 'EXISTS')
" 2>/dev/null || echo "ERROR")

if [ "$INIT_CHECK" = "FRESH" ] && [ "$ALLOW_INIT_DB" = "true" ]; then
    echo "🌱 Fresh DB detected + ALLOW_INIT_DB=true → Running init_db.py"
    python database/init_db.py
elif [ "$INIT_CHECK" = "FRESH" ]; then
    echo "⚠️  Fresh DB detected, but ALLOW_INIT_DB≠true. Skipping init_db.py"
    echo "   Чтобы инициализировать БД, запусти контейнер с: -e ALLOW_INIT_DB=true"
fi

# Применение миграций Alembic (основной механизм)
echo "🔄 Applying Alembic migrations..."
alembic upgrade head

# Запуск бота
echo "▶️  Starting bot..."
exec "$@"