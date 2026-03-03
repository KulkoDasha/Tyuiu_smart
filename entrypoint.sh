#!/bin/sh
set -e

echo "=== Starting Tiumnichka Bot ==="

if [ -n "$DB_CREDENTIALS_OVERRIDE" ]; then
    export DB_CREDENTIALS="$DB_CREDENTIALS_OVERRIDE"
fi

echo "Waiting for database..."
MAX_RETRIES=30
RETRY_COUNT=0
until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Database not ready after $MAX_RETRIES attempts"
        exit 1
    fi
    sleep 2
done
echo "Database ready"

echo "Applying Alembic migrations..."
alembic upgrade head

echo "Starting bot..."
exec "$@"