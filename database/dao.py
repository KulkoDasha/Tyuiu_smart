import logging

from .database_service import connection
from .models import Users, Event_applications 
from sqlalchemy import select, update
from typing import Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, time, date, timedelta

logger = logging.getLogger(__name__)

@connection
async def db_set_user(session, 
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
                   ) -> Optional[Tuple[bool, str, Optional[int]]]:
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
            return False, "Участник уже зарегистрирован", None
        
        if existing_email:
            logger.info(f"Почта {email} уже используется")
            return False, "Почта уже зарегистрирована", None

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
        await session.flush()  
        user_id = new_user.id

        await session.commit()
        logger.info(f"Зарегистрирован студент с TG ID {tg_id}, ID в БД: {user_id}")
        return True, "Пользователь успешно добавлен", user_id
    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при добавлении студента: {e}")
        await session.rollback()
        return False, f"Ошибка базы данных: {str(e)}", None
    

@connection
async def db_delete_graduated_users(session) -> Tuple[int, str]:
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

        # Сбрасываем баланс всех оставшихся пользователей до 0.0
        remaining_users = await session.scalars(
            select(Users)
            .where(Users.end_year > current_year)  # Те, кто еще учится
        )
        remaining_users_list = remaining_users.all()
        
        reset_count = 0
        for user in remaining_users_list:
            if user.tiukoins != 0.0:  # Обновляем только если баланс не 0
                user.tiukoins = 0.0
                reset_count += 1
        
        await session.commit()
        logger.info(f"Удалено {deleted_count} выпускников")
        return deleted_count, f"Удалено {deleted_count} выпускников. сброшено балансов {reset_count}"
    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при удалении выпускников: {e}")
        await session.rollback()
        return 0, f"Ошибка базы данных: {str(e)}"


@connection 
async def db_get_user_full_name(session, tg_id_str:str ) -> str:
    """
    Получение ФИО студента по его tg ID
    """
    tg_id = int(tg_id_str)
    full_name = await session.scalar(select(Users.full_name).where(Users.tg_id == tg_id))
    if full_name:
        return full_name
    else:
        return ""
    
@connection
async def db_user_exists(session, tg_id_str: str) -> bool:
    """
    Проверяет, существует ли пользователь с заданным tg_id
    Возвращает True если существует, False если нет
    """
    tg_id = int(tg_id_str)
    exists = await session.scalar(
        select(1).where(Users.tg_id == tg_id)
    )
    return exists is not None
    

@connection
async def db_submit_event_application (session,
                                    tg_id_str: str,
                                    event_direction: str,
                                    event_name: str,
                                    date_of_event: str,
                                    event_place: str,
                                    event_role: str
                                    ) -> Tuple[int, str]:
    """
    Метод для добавления заявки пользователя по мероприятию (без подтверждения от модератора)
    Проверка факта регистрации пользователя и отсутствия у него уже существующей заявки на данное мероприятие. 
    """
    
    tg_id = int(tg_id_str)
    full_name = await db_get_user_full_name(tg_id_str)
    bool_user_exists = await db_user_exists(tg_id_str)

    try:
        if bool_user_exists == False:
            return -1, f"Пользователь с ID: {tg_id} не зарегестрирован"
    except Exception as e:
        logger.error(f"Ошибка при проверке пользователя {tg_id}: {e}")
        return -1, f"Ошибка при проверке пользователя: {str(e)}"
    

    try:
        event_date = datetime.strptime(date_of_event, "%d.%m.%Y")

        existing_application = await session.scalar(
            select(Event_applications).where(
                Event_applications.tg_id == tg_id,
                Event_applications.event_name == event_name,
                Event_applications.date_of_event == event_date
            ))

        if existing_application:
            existing_application_status = existing_application.event_application_status
            if existing_application_status in ['Принята', 'На рассмотрении ']:
                return -1, "Заявка уже существует"
    except Exception as e:
        logger.error(f"Ошибка при проверке дубликатов заявки {tg_id}: {e}")
        return -1, f"Ошибка при проверке заявок: {str(e)}"
    
    try:        
        new_event_application = Event_applications(
            tg_id = tg_id,
            full_name = full_name,
            event_direction = event_direction,
            event_name = event_name,
            date_of_event = event_date,
            event_place = event_place,
            event_role = event_role,
            event_application_status = "На рассмотрении",
            amount_tiukoins = 0.0,
            moderator = "Не назначен"
        )
        session.add(new_event_application)
        await session.flush() 
        application_id = new_event_application.id
        
        await session.commit()

        logger.info(f"Студент с ID {tg_id} подал заявку")
        return application_id, "Заявка успешно подана"
    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при добавлении заявки студентом: {e}")
        await session.rollback()
        return -1, f"Ошибка базы данных: {str(e)}"
    

@connection
async def db_approve_application(
    session,
    application_id: int,
    moderator_username: str,
    tiukoins_amount: float
) -> Tuple[bool, str]:
    """
    Модератор принимает заявку и начисляет тиукоины
    """
    try:
        # ✅ 1. Обновляем заявку через CORE (без ORM!)
        result = await session.execute(
            update(Event_applications)
            .where(
                Event_applications.id == application_id,
                Event_applications.event_application_status == 'На рассмотрении'
            )
            .values(
                event_application_status='Принята',
                moderator=moderator_username,
                amount_tiukoins=tiukoins_amount
            )
            .returning(Event_applications.tg_id)
        )
        
        app_data = result.fetchone()
        if not app_data:
            return False, "Заявка не найдена или уже обработана"

        tg_id = app_data.tg_id

        # ✅ 2. Обновляем баланс
        await session.execute(
            update(Users)
            .where(Users.tg_id == tg_id)
            .values(tiukoins=Users.tiukoins + tiukoins_amount)
        )

        await session.commit()
        return True, "Заявка принята и тиукоины начислены"

    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка при принятии заявки {application_id}: {e}")
        return False, f"Ошибка базы данных: {str(e)}"


@connection
async def db_reject_application(
    session,
    application_id: int,
    moderator_username: str
) -> Tuple[bool, str]:
    """
    Модератор отклоняет заявку
    """
    try:
        # 1. Находим заявку
        result = await session.execute(
            select(Event_applications).where(Event_applications.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            return False, "Заявка не найдена"
        
        # 2. Проверяем статус
        if application.event_application_status != 'На рассмотрении':
            return False, f"Заявка уже имеет статус: {application.event_application_status}"
        
        # 3. Обновляем заявку
        application.event_application_status = 'Отклонена'
        application.moderator = moderator_username
        application.amount_tiukoins = 0.0 
        
        await session.commit()
        
        logger.info(
            f"Заявка #{application_id} отклонена модератором @{moderator_username}"
        )
        
        return True, "Заявка отклонена"
        
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка при отклонении заявки {application_id}: {e}")
        return False, f"Ошибка базы данных: {str(e)}"
    

@connection
async def db_deduct_tiukoins(session, tg_id_str: str, spend_amount: float, name_of_item: str) -> Tuple[bool, str]:
    """
    Списание тиукоинов у пользователя при заказе поощрения
    """
    try:
            
        tg_id = int(tg_id_str)
        
        # 2. Получаем пользователя
        result = await session.execute(
            select(Users).where(Users.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False, f"Пользователь с TG ID {tg_id} не найден"
        
        # 3. Проверяем баланс
        current_balance = user.tiukoins
        
        if current_balance < spend_amount:
            return False, f"Недостаточно тиукоинов. Ваш баланс: {current_balance:.1f}, требуется: {spend_amount:.1f}"
        
        # 4. Рассчитываем новый баланс в переменной
        new_balance = current_balance - spend_amount
        
        # 5. Обновляем поле
        user.tiukoins = new_balance
        
        # 6. Сохраняем
        await session.commit()
        
        logger.info(
            f"✅ Списано {spend_amount} тиукоинов у пользователя {tg_id}. "
            f"Поощрение: {name_of_item}. "
            f"Было: {current_balance:.1f}, стало: {new_balance:.1f}"
        )
        
        return True, f"✅ Успешно! Списано {spend_amount} тиукоинов. Новый баланс: {new_balance:.1f}"
        
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка при списании тиукоинов у пользователя {tg_id}: {e}")
        return False, f"Ошибка базы данных: {str(e)}"
    except Exception as e:
        logger.error(f"Неожиданная ошибка при списании тиукоинов: {e}")
        return False, f"Ошибка: {str(e)}"
    


@connection
async def db_get_user_balance(session, tg_id_str: str) -> float:
    """
    Получает текущий баланс тиукоинов пользователя
    """
    try:
        # Преобразуем строку в число
        tg_id = int(tg_id_str)
        
        # Получаем пользователя
        result = await session.execute(
            select(Users).where(Users.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return 0.0
        
        return user.tiukoins
    
    except Exception as e:
        logger.error(f"Ошибка получения баланса пользователя {tg_id}: {e}")
        return 0.0
    
@connection
async def db_return_tiukoins(session,
                          tg_id_str: str,
                          item_price_str: str) -> Tuple[bool, str]:
    """
    Возврат тиукоинов пользователю при отклонении
    """
    try: 
        tg_id = int(tg_id_str)
        item_price = float(item_price_str)

        result = await session.execute(
            select(Users).where(Users.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False, f"Пользователь с TG ID {tg_id} не найден"
        
        if item_price <= 0:
            return False, f"Некорректная сумма возврата: {item_price}. Сумма должна быть положительной."
        
        old_balance = user.tiukoins
        new_balance = old_balance + item_price
        user.tiukoins = new_balance
        await session.commit()

        logger.info(f"✅ Возвращено {item_price} тиукоинов пользователю {tg_id}. ")
        return True, f"✅ Успешно! Возвращено {item_price} тиукоинов. Новый баланс: {new_balance:.1f}"
    
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"❌ Ошибка БД при возврате тиукоинов пользователю {tg_id}: {e}")
        return False, f"Ошибка базы данных: {str(e)}"
    
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при возврате тиукоинов: {e}")
        return False, f"Ошибка: {str(e)}"