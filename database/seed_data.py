from sqlalchemy import insert
import database
import models
engine = database.engine
Roles = models.Roles
from sqlalchemy import func
from sqlalchemy import select

async def seed_roles():
    """Заполнение таблицы roles начальными данными."""
    async with engine.begin() as conn:
        print("🔄 Подключение к БД...")  # ДОБАВЬТЕ ЭТУ СТРОКУ
        result = await conn.execute(select(func.count()).select_from(Roles))
        count = result.scalar()
        print(f"📊 Найдено ролей: {count}") 
        
        if count == 0:  # Заполняем только если таблица пуста
            roles_data = [
                {"id": 1, "role": "Зритель", "base_value_tiucoins": 0.2},
                {"id": 2, "role": "Участник", "base_value_tiucoins": 1.0},
                {"id": 3, "role": "Финалист", "base_value_tiucoins": 3.0},
                {"id": 4, "role": "Победитель", "base_value_tiucoins": 10.0},
                {"id": 5, "role": "Волонтёр", "base_value_tiucoins": 2.0},
                {"id": 6, "role": "Соорганизатор", "base_value_tiucoins": 3.0},
                {"id": 7, "role": "Организатор", "base_value_tiucoins": 5.0},
                {"id": 8, "role": "Наставник", "base_value_tiucoins": 3.0},
                {"id": 9, "role": "Спикер", "base_value_tiucoins": 4.0},
                {"id": 10, "role": "Руководитель", "base_value_tiucoins": 8.0},
            ]
            
            for role_data in roles_data:
                stmt = insert(Roles).values(**role_data)
                await conn.execute(stmt)
            
            await conn.commit()
            print("Таблица roles заполнена начальными данными")
        else:
            print("Таблица roles уже содержит данные")

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_roles())
