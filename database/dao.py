from create_bot import logger
from .base import connection
from .models import Users, Event_applications 
from sqlalchemy import select
from typing import Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, time, date, timedelta

@connection
async def set_user(session, 
                   tg_id: str, 
                   full_name: str, 
                   institute: str, 
                   direction: str, 
                   group: str,
                   start_year_str: str,
                   end_year_str: str,
                   phone_number:str,
                   email: str,
                   moderator_username: str
                   ) -> Optional[Tuple[bool, str]]:
    """Метод для добавления нового пользователя (проверка по tg_id, почте)"""
    try:
        tg_id_int = int(tg_id)
        start_year = int(start_year_str)
        end_year = int(end_year_str)

        current_year = datetime.now().year
        user = await session.scalar(select(Users).where(Users.tg_id == tg_id))
        existing_email = await session.scalar(select(Users).where(Users.email == email))

        if start_year > current_year:
            return False, f"Год начала обучения ({start_year}) не может быть больше текущего года ({current_year})"
        
        if user:
            logger.info(f"Студент с ID {tg_id_int} уже существует")
            return False, "Пользователь уже зарегистрирован"
        
        if existing_email:
            logger.info(f"Почта {email} уже используется")
            return False, "Почта уже зарегистрирована"

        new_user = User(
            tg_id = tg_id_int,
            full_name = full_name,
            institute = institute,
            direction = direction,
            group = group,
            start_year = start_year,
            end_year = end_year,
            phone_number = phone_number,
            email = email,
            tiucoins = 0.0,
            approval_date = datetime.now(),
            moderator_username = moderator_username
        )
        session.add(new_user)
        await session.commit()
        logger.info(f"Зарегистрировал студент с ID {tg_id_int}")
        return None
    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при добавлении студента: {e}")
        await session.rollback()
        return False, f"Ошибка базы данных: {str(e)}"