# database/migration/env.py
"""
Alembic environment configuration for Tiumnichka Bot.
Supports asyncpg for app, psycopg2 for migrations.
Reads DB_CREDENTIALS from environment (.env via python-dotenv).
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from urllib.parse import urlparse, urlunparse

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# === PATH SETUP ===
# Добавляем корень проекта в sys.path для импорта моделей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# === IMPORTS ===
# Импорт Base из твоих моделей (укажи правильный путь!)
from database.models import Base  # <-- Проверь, что путь верный!

# Загрузка переменных окружения из .env
try:
    from dotenv import load_dotenv
    # Загружаем .env из корня проекта
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    load_dotenv(env_path)
except ImportError:
    # Если dotenv не установлен — полагаемся на системные env
    pass

# === ALEMBIC CONFIG ===
config = context.config

# Настройка логгера Alembic из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata для автогенерации миграций (сравниваем с моделями)
target_metadata = Base.metadata


def get_url() -> str:
    """
    Получает DB_CREDENTIALS из окружения и адаптирует для Alembic.
    
    """
    url = os.getenv("DB_CREDENTIALS")
    
    if not url:
        raise RuntimeError(
            "❌ Переменная окружения DB_CREDENTIALS не задана!\n"
            "Проверь файл .env или передай переменную при запуске."
        )
    
    # Парсим URL для замены драйвера
    parsed = urlparse(url)
    
    scheme = parsed.scheme
    if scheme == "postgresql+asyncpg":
        scheme = "postgresql+psycopg2"
    elif scheme == "postgresql" and "asyncpg" not in url:
        # Если драйвер не указан — явно добавляем psycopg2
        scheme = "postgresql+psycopg2"
    
    # Собираем URL обратно
    url_sync = urlunparse((
        scheme,           # driver
        parsed.netloc,    # user:pass@host:port
        parsed.path,      # /dbname
        parsed.params,
        parsed.query,     # ?sslmode=disable
        parsed.fragment
    ))
    
    return url_sync


def run_migrations_offline() -> None:
    """
    Запуск миграций в offline-режиме.
    Генерирует SQL-скрипт без подключения к БД.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,          # Сравнивать типы колонок
        compare_server_default=True, # Сравнивать DEFAULT-значения
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Применяет миграции к реальной БД через sync-connection.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # Важно для SQLite и некоторых миграций на PostgreSQL
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Асинхронное подключение к БД для применения миграций.
    Используем async_engine_from_config, но внутри — sync-операции.
    """
    # Получаем URL с заменённым драйвером
    sync_url = get_url()
    
    # Создаём конфиг для engine, переопределяя sqlalchemy.url
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = sync_url
    
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Запуск миграций в online-режиме (подключение к реальной БД).
    """
    asyncio.run(run_async_migrations())


# === MAIN ENTRY POINT ===
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()