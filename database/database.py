from sqlalchemy import func
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession

# Строка подключения для PostgreSQL с asyncpg (локально)
engine = create_async_engine(
    url='postgresql+asyncpg://username:password@localhost:5432/dbname'
)

async_session = async_sessionmaker(engine, class_=AsyncSession)

class Base(AsyncAttrs, DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())