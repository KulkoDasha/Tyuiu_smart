from .database import async_session, engine, Base


def connection(func):
    """декоратора для всех функций для взаимодействия с базой данных."""
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)

    return wrapper


async def create_tables():
    """создание таблиц в бд"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)