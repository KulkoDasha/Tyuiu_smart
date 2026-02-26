import asyncio
from database.database_service import create_tables

async def main():
    print("Создание таблиц...")
    await create_tables()
    print("Готово!")

if __name__ == "__main__":
    asyncio.run(main())