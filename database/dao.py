import logging

from .database_service import connection
from .models import Users, Event_applications 
from sqlalchemy import select
from typing import Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, time, date, timedelta

logger = logging.getLogger(__name__)

@connection
async def set_user(session, 
                   tg_id_str: str, 
                   full_name: str, 
                   institute: str, 
                   direction: str, 
                   group: str,
                   course_str: str,
                   start_year_str: str,
                   end_year_str: str,
                   phone_number:str,
                   email: str,
                   moderator_username: str
                   ) -> Optional[Tuple[bool, str]]:
    """Метод для добавления нового пользователя (проверка по tg_id и почте)"""
    try:
        tg_id = int(tg_id_str)
        start_year = int(start_year_str)
        end_year = int(end_year_str)
        course = int(course_str)
        user = await session.scalar(select(Users).where(Users.tg_id == tg_id))
        existing_email = await session.scalar(select(Users).where(Users.email == email))

        if user:
            logger.info(f"Студент с ID {tg_id} уже существует")
            return False, "Пользователь уже зарегистрирован"
        
        if existing_email:
            logger.info(f"Почта {email} уже используется")
            return False, "Почта уже зарегистрирована"

        new_user = Users(
            tg_id = tg_id,
            full_name = full_name,
            institute = institute,
            direction = direction,
            group = group,
            course = course,
            start_year = start_year,
            end_year = end_year,
            phone_number = phone_number,
            email = email,
            tiukoins = 0.0,
            approval_date = datetime.now(),
            moderator_username = moderator_username
        )
        session.add(new_user)
        await session.commit()
        logger.info(f"Зарегистрировал студент с ID {tg_id}")
        return None
    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при добавлении студента: {e}")
        await session.rollback()
        return False, f"Ошибка базы данных: {str(e)}"
    

@connection
async def delete_graduated_users(session) -> Tuple[int, str]:
    """ Удаляет пользователей, у которых год окончания обучения равен текущему году.
     Возвращает: (количество_удаленных, сообщение) """
    try:
        from datetime import datetime
        current_year = datetime.now().year
        
        # Находим всех студентов, которых нужно удалить
        graduated_users = await session.scalars(
            select(Users)
            .where(Users.end_year == current_year)
        )
        users_to_delete = graduated_users.all()
        deleted_count = len(users_to_delete)
        
        if deleted_count == 0:
            logger.info("Выпускников для удаления не найдено")
            return 0, "Выпускников для удаления не найдено"
        
        # Удаляем связанных заявки (cascade delete сработает автоматически)
        for user in users_to_delete:
            logger.info(f"Удаляю выпускника: {user.full_name} (tg_id: {user.tg_id})")
            await session.delete(user)
        
        await session.commit()
        logger.info(f"Удалено {deleted_count} выпускников")
        return deleted_count, f"Удалено {deleted_count} выпускников"
    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при удалении выпускников: {e}")
        await session.rollback()
        return 0, f"Ошибка базы данных: {str(e)}"
