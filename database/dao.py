import logging

from .database_service import connection
from .models import Users, Event_applications 
from sqlalchemy import select, update, delete
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
async def db_delete_all_users(session) -> Tuple[bool, str]:
    """
    Удаляет ВСЕХ пользователей из базы данных
    Сначала удаляет все связанные заявки, потом пользователей
    """
    try:
        # 1. Сначала удаляем ВСЕ заявки
        result_apps = await session.execute(delete(Event_applications))
        deleted_apps_count = result_apps.rowcount
        
        # 2. Потом удаляем ВСЕХ пользователей
        result_users = await session.execute(delete(Users))
        deleted_users_count = result_users.rowcount
        
        await session.commit()
        
        logger.warning(f"💥 УДАЛЕНО ВСЕ! Заявки: {deleted_apps_count}, Пользователи: {deleted_users_count}")
        return True, f"✅ Успешно удалено {deleted_users_count} пользователей и {deleted_apps_count} заявок"
    
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"❌ Ошибка БД при удалении всех пользователей: {e}")
        return False, f"Ошибка БД: {str(e)}"
    
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при удалении: {e}")
        return False, f"Ошибка: {str(e)}"


@connection 
async def db_get_user_full_name(session, tg_id_str:str ) -> str:
    """
    Получение ФИО студента по его tg ID
    """
    tg_id = int(tg_id_str)
    full_name = await session.scalar(select(Users.full_name).where(Users.tg_id == tg_id))
    if full_name:
        return str(full_name)
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
) -> Tuple[bool, str, float]:
    """
    Модератор принимает заявку и начисляет тиукоины
    """
    try:

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
            return False, "Заявка не найдена или уже обработана", 0.0

        tg_id = app_data.tg_id

        await session.execute(
            update(Users)
            .where(Users.tg_id == tg_id)
            .values(tiukoins=Users.tiukoins + tiukoins_amount)
        )

        await session.commit()
        return True, "Заявка принята и тиукоины начислены", tiukoins_amount

    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка при принятии заявки {application_id}: {e}")
        return False, f"Ошибка базы данных: {str(e)}", 0.0


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
    



async def db_get_user_balance(session, tg_id_str: str) -> float:
    """
    Получает текущий баланс тиукоинов пользователя
    """
    try:
        # Преобразуем строку в число
        tg_id = int(tg_id_str)
        
        # Получаем пользователя
        result = await session.execute(select(Users).where(Users.tg_id == tg_id))
        user = result.scalars().first()
        
        return user.tiukoins if user else 0.0
    
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
    

@connection
async def db_delete_user_by_tg_id(session, tg_id_str: str) -> Tuple[bool, str, Optional[int]]:
    """
    Удаляет пользователя по tg_id.
    """
    try:
        tg_id = int(tg_id_str)
        
        # 1. Находим пользователя
        result = await session.execute(
            select(Users).where(Users.tg_id == tg_id)
        )
        user = result.scalars().first()
        
        if not user:
            logger.info(f"Пользователь с tg_id {tg_id} не найден")
            return False, f"Пользователь с ID {tg_id} не найден", None
        
        logger.info(f"Удаляю пользователя: {user.full_name} (tg_id: {tg_id})")
        
        # 2. Удаляем (cascade delete удалит связанные заявки автоматически)
        user_db_id = user.id

        await session.delete(user)
        await session.commit()
        
        logger.info(f"✅ Успешно удален пользователь tg_id={tg_id}")
        return True, f"✅ Удален пользователь: {user.full_name} ({user.tg_id})", user_db_id
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления пользователя {tg_id_str}: {e}")
        await session.rollback()
        return False, f"❌ Ошибка: {str(e)}", None

    
@connection
async def db_get_application_history(session, tg_id_str: str) -> Tuple[bool, list[list]]:
    """
    Последние заявки пользователя за последние 3 месяца (по тг айди)
    Возвращает: направление, название мероприятия, дату, роль, ТИУкоины, статус 
    """
    try:
        tg_id = int(tg_id_str)
        three_months_ago = datetime.now() - timedelta(days=90)

        stmt = select(Event_applications).where(
            Event_applications.tg_id == tg_id,
            Event_applications.date_of_event >= three_months_ago
        ).order_by(Event_applications.date_of_event.desc())

        result = await session.execute(stmt)
        applications = result.scalars().all()

        apps_list = []
        for app in applications:
            apps_list.append([
                app.event_direction,
                app.event_name,
                app.date_of_event.strftime('%d-%m-%Y'),
                app.event_role,
                app.amount_tiukoins,
                app.event_application_status
            ])

        logger.info(f"📋 Заявки пользователя {tg_id}: найдено {len(apps_list)} за 3 месяца")
        return True, apps_list
    
    except SQLAlchemyError as e:
        logger.error(f"❌ Ошибка БД при получении заявок пользователя {tg_id}: {e}")
        return False, []

    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при получении заявок: {e}")
        return False, []
    

@connection
async def db_get_all_user_tg_ids(session) -> Tuple[bool, list[int]]:
    """
    Возвращает список всех TG ID пользователей из базы данных 
    """
    try:
        stmt = select(Users.tg_id) 
        
        result = await session.execute(stmt)
        tg_ids = result.scalars().all()
        all_ids = [str(id) for id in tg_ids]
        
        logger.info(f"📋 Всего пользователей в БД: {len(all_ids)}")
        return True, list(all_ids)  

    except SQLAlchemyError as e:
        logger.error(f"❌ Ошибка БД при получении всех TG ID: {e}")
        return False, []
    
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return False, []
