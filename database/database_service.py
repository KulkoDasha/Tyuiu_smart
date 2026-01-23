from database.models import Base
from database.database import engine, async_session

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

    import seed_data 
    await seed_data.seed_roles() 