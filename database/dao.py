import logging

from .database_service import connection
from .models import Users, Event_applications, Issuance_of_rewards, Catalog_of_reward
from sqlalchemy import select, update, delete, text
from typing import Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

@connection
async def db_set_user(session, 
                   tg_id_str: str, 
                   full_name: str, 
                   username: str,
                   ) -> Optional[Tuple[bool, str, Optional[int], Optional[str]]]:
    """
    Метод для добавления нового пользователя (проверка по tg_id и уникальной почте)
    """

    try:
        tg_id = int(tg_id_str)

        new_user = Users(
            tg_id = tg_id,
            full_name = full_name,
            username = username,
            tiukoins = 0.0,
            approval_date = datetime.now(),
            moderator_username = "Не указано"

        )
        session.add(new_user)
        await session.flush()  
        user_id = new_user.id

        await session.commit()
        return True, f"Пользователь {tg_id} успешно добавлен в БД (ID: {user_id})", user_id, "✅ Успешно"
    
    except SQLAlchemyError as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", None, f"Ошибка БД при добавлении пользователя: {str(e)}"
    

@connection
async def db_delete_all_users(session) -> Tuple[bool, str, Optional[str]]:
    """
    Удаляет ВСЕХ пользователей из базы данных, все заявки на мероприятия и заявки на выдачу поощрения.
    Сначала удаляет все связанные записи, потом пользователей
    """

    try:
        # Удаляем все заявки на выдачу поощрений 
        result_issuances = await session.execute(delete(Issuance_of_rewards))
        deleted_issuances_count = result_issuances.rowcount
        
        # Удаляем все заявки на мероприятия
        result_apps = await session.execute(delete(Event_applications))
        deleted_apps_count = result_apps.rowcount
        
        # Удаляем всех пользователей
        result_users = await session.execute(delete(Users))
        deleted_users_count = result_users.rowcount
        
        await session.commit()

        # Сбрасываем последовательности ID для всех таблиц
        await session.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
        await session.execute(text("ALTER SEQUENCE event_applications_id_seq RESTART WITH 1"))
        await session.execute(text("ALTER SEQUENCE issuance_of_rewards_id_seq RESTART WITH 1"))
        await session.commit()
        
        return True, f"✅ Успешно удалено {deleted_users_count} пользователей, {deleted_apps_count} заявок и {deleted_issuances_count} выдач поощрений", "✅ Успешно"
    
    except SQLAlchemyError as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Ошибка БД при удалении всех пользователей: {str(e)}"
    
    except Exception as e:
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Критическая ошибка БД при удалении всех пользователей: {str(e)}"


@connection 
async def db_get_user_full_name(session, tg_id_str:str ) -> str:
    """Получение ФИО студента по его tg_id"""

    tg_id = int(tg_id_str)
    full_name = await session.scalar(select(Users.full_name).where(Users.tg_id == tg_id))
    if full_name:
        return str(full_name)
    else:
        return ""
    
@connection
async def db_user_exists(session, tg_id_str: str) -> str:
    """
    Проверяет статус пользователя в системе.
    
    Возвращает:
        "not_registered" — записи о пользователе нет в БД (можно регистрироваться)
        "pending"        — запись есть, но moderator_username == "Не указано" (ждать одобрения)
        "approved"       — запись есть и moderator_username != "Не указано" (доступ открыт)
    """
    tg_id = int(tg_id_str)
    
    # Получаем пользователя из БД
    user = await session.scalar(select(Users).where(Users.tg_id == tg_id))
    
    if user is None:
        return "not_registered"
    
    if user.moderator_username == "Не указано":
        return "pending"
    
    return "approved"

@connection
async def db_submit_event_application (session,
                                    tg_id_str: str,
                                    event_direction: str,
                                    event_name: str,
                                    date_of_event: str,
                                    event_place: str,
                                    event_role: str,
                                    username: str
                                    ) -> Tuple[int, str, Optional[str]]:
    """
    Метод для добавления заявки пользователя по мероприятию (без подтверждения от модератора)
    Проверка факта регистрации пользователя и отсутствия у него уже существующей заявки на данное мероприятие
    """
    
    tg_id = int(tg_id_str)
    full_name = await db_get_user_full_name(tg_id_str)
    bool_user_exists = await db_user_exists(tg_id_str)

    try:
        if bool_user_exists != "approved":
            return -1, f"Пользователь с ID: {tg_id} не зарегестрирован", None
    except Exception as e:
        return -1, f"❌ Ошибка базы данных. Обратитесь в поддержку /support.", f"Ошибка при проверке пользователя {tg_id}: {str(e)}"
    

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
                return -1, "Такая заявка уже существует", None
    except Exception as e:
        return -1, f"❌ Ошибка базы данных. Обратитесь в поддержку /support.", f"Ошибка БД при проверке дубликатов заявки {tg_id}: {str(e)}"
    
    try:        
        new_event_application = Event_applications(
            tg_id = tg_id,
            full_name = full_name,
            username = username,
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

        return application_id, f"Пользователь {tg_id} подал заявку", "✅ Успешно"
    
    except SQLAlchemyError as e:
        await session.rollback()
        return -1, f"❌ Ошибка базы данных. Обратитесь в поддержку /support.", f"Ошибка при добавлении заявки студентом {tg_id}: {e}"
    

@connection
async def db_approve_application(
    session,
    application_id: int,
    moderator_username: str,
    tiukoins_amount: float
) -> Tuple[bool, str, float, Optional[str]]:
    """Модератор принимает заявку и начисляет ТИУкоины"""

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
            return False, "Заявка не найдена или уже обработана", 0.0, None

        tg_id = app_data.tg_id

        await session.execute(
            update(Users)
            .where(Users.tg_id == tg_id)
            .values(tiukoins=Users.tiukoins + tiukoins_amount)
        )

        await session.commit()
        return True, "Заявка принята и ТИУкоины начислены", tiukoins_amount, "✅ Успешно"

    except Exception as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", 0.0, f"Ошибка при принятии заявки {application_id}: {str(e)}"


@connection
async def db_reject_application(
    session,
    application_id: int,
    moderator_username: str
) -> Tuple[bool, str, Optional[str]]:
    """Модератор отклоняет заявку"""

    try:
        # Находим заявку
        result = await session.execute(
            select(Event_applications).where(Event_applications.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            return False, "Заявка не найдена", None
        
        # Проверяем статус
        if application.event_application_status != 'На рассмотрении':
            return False, f"Заявка уже имеет статус: {application.event_application_status}", None
        
        # Обновляем заявку
        application.event_application_status = 'Отклонена'
        application.moderator = moderator_username
        application.amount_tiukoins = 0.0 
        
        await session.commit()
        
        return True, f"Заявка №{application_id} отклонена модератором @{moderator_username}", "✅ Успешно"
        
    except SQLAlchemyError as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Ошибка БД при отклонении заявки {application_id}: {str(e)}"
    

@connection
async def db_deduct_tiukoins(
    session,
    tg_id_str: str,
    spend_amount: float) -> Tuple[bool, str, Optional[str]]:
    """Списание ТИУкоинов у пользователя """

    try:
            
        tg_id = int(tg_id_str)
        
        # Получаем пользователя
        result = await session.execute(
            select(Users).where(Users.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False, f"Пользователь с TG_ID:{tg_id} не найден.", None
        
        # Проверяем баланс
        current_balance = user.tiukoins
        
        if current_balance < spend_amount:
            return False, f"Недостаточно ТИУкоинов.\nБаланс: {current_balance:.1f}. Требуется: {spend_amount:.1f}", None
        
        # Рассчитываем новый баланс в переменной
        new_balance = current_balance - spend_amount
        
        # Обновляем поле
        user.tiukoins = new_balance
        
        # Сохраняем
        await session.commit()
        
        return True, f"✅ Успешно! Списано {spend_amount} ТИУкоинов у пользователя {tg_id}\n. Новый баланс: {new_balance:.1f}", "✅ Успешно"
        
    except SQLAlchemyError as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Ошибка БД при списании ТИУкоинов у пользователя {tg_id}: {str(e)}"
    except Exception as e:
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Ошибка БД при списании ТИУкоинов у пользователя {tg_id}: {str(e)}"

@connection
async def db_add_tiukoins(session,
                          tg_id_str: str,
                          spend_amount: float) -> Tuple[bool, str, Optional[str]]:
    """Добавление ТИУкоинов пользователю"""

    try:
            
        tg_id = int(tg_id_str)
        
        # Получаем пользователя
        result = await session.execute(
            select(Users).where(Users.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False, f"Пользователь с TG ID {tg_id} не найден", None
        
        # Получаем баланс
        current_balance = user.tiukoins
        
        # Рассчитываем новый баланс в переменной
        new_balance = current_balance + spend_amount
        
        # Обновляем поле
        user.tiukoins = new_balance
        
        # Сохраняем
        await session.commit()
        
        return True, f"✅ Успешно! добавлено {spend_amount} ТИУкоинов пользователю {tg_id}. Новый баланс: {new_balance:.1f}", "✅ Успешно"
        
    except SQLAlchemyError as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Ошибка БД при добавлении ТИУкоинов у пользователя {tg_id}: {str(e)}"
    except Exception as e:
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Ошибка БД при добавлении ТИУкоинов: {str(e)}"

@connection
async def db_get_user_balance(session, tg_id_str: str) -> Tuple[float, str, Optional[str]]:
    """Получает текущий баланс ТИУкоинов пользователя"""

    try:
        # Преобразуем строку в число
        tg_id = int(tg_id_str)
        
        # Получаем пользователя
        result = await session.execute(select(Users).where(Users.tg_id == tg_id))
        user = result.scalars().first()
        
        return user.tiukoins if user else 0.0, "Баланс успешно получен", "✅ Успешно"
    
    except Exception as e:
        return 0.0, f"❌ Ошибка получения баланс. Обратитесь в /support. ", f"Ошибка БД при получении баланса пользователя {tg_id}: {str(e)}"
    
@connection
async def db_reject_issuance(
    session,
    tg_id_str: str,
    issuance_id: int,
    moderator_username: str
) -> Tuple[bool, str, Optional[str]]:
    """
    Возврат ТИУкоинов пользователю при отклонении заявки на поощрение
    - Возвращает ТИУкоины пользователю
    - Увеличивает количество товара в каталоге на 1
    - Меняет статус заявки на "Отклонено"
    - Записывает moderator_username в заявку
    """
    try: 
        tg_id = int(tg_id_str)

        # 1. Получаем заявку на выдачу
        issuance_result = await session.execute(
            select(Issuance_of_rewards).where(Issuance_of_rewards.id == issuance_id)
        )
        issuance = issuance_result.scalar_one_or_none()

        if not issuance:
            return False, f"Заявка с ID {issuance_id} не найдена.", None

        # 2. Получаем товар из каталога по reward_id из заявки
        reward_result = await session.execute(
            select(Catalog_of_reward).where(Catalog_of_reward.id == issuance.reward_id)
        )
        reward = reward_result.scalar_one_or_none()

        if not reward:
            return False, f"Товар с ID {issuance.reward_id} не найден в каталоге.", None

        # 3. Получаем пользователя
        user_result = await session.execute(
            select(Users).where(Users.tg_id == tg_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False, f"Пользователь с TG ID {tg_id} не найден", None
        
        # 4. Проверяем, что заявка еще не обработана
        if issuance.status != "Ожидает выдачи":
            return False, f"Заявка #{issuance_id} уже обработана (статус: {issuance.status})", None
        
        # 5. Возвращаем ТИУкоины пользователю
        old_balance = user.tiukoins
        refund_amount = float(issuance.price)
        new_balance = old_balance + refund_amount
        user.tiukoins = new_balance

        # 6. Увеличиваем количество товара на 1
        old_quantity = reward.count
        reward.count += 1

        # 7. Обновляем статус заявки и модератора
        issuance.status = "Отклонено"
        issuance.moderator_username = moderator_username
        
        # 8. Сохраняем все изменения
        await session.commit()

        return (True,
                f"Заявка на получение поощрения откланена ",
                f"✅ Успешно")
    
    except SQLAlchemyError as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Ошибка БД при возврате ТИУкоинов пользователю {tg_id}: {str(e)}"
    except Exception as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Неожиданная ошибка БД при возврате ТИУкоинов: {str(e)}"
    

@connection
async def db_delete_user_by_tg_id(session, tg_id_str: str) -> Tuple[bool, str, Optional[int], Optional[str]]:
    """Удаляет пользователя по tg_id"""

    try:
        tg_id = int(tg_id_str)
        
        # Находим пользователя
        result = await session.execute(
            select(Users).where(Users.tg_id == tg_id)
        )
        user = result.scalars().first()
        
        if not user:
            return False, f"Пользователь {tg_id} не найден", None, None
        
        # Удаляем (cascade delete удалит связанные заявки автоматически)
        user_db_id = user.id

        await session.delete(user)
        await session.commit()
        
        return True, f"✅ Удален пользователь: {user.full_name} ({user.tg_id})", user_db_id, "✅ Успешно"
        
    except Exception as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", None, f"Ошибка БД при удалении пользователя {tg_id_str}: {str(e)}"

    
@connection
async def db_get_application_history(session, tg_id_str: str) -> Tuple[bool, list[list], Optional[str]]:
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

        return True, apps_list, f"Заявки пользователя {tg_id}: найдено {len(apps_list)} за 3 месяца", "✅ Успешно"
    
    except SQLAlchemyError as e:
        return False, [], f"❌ Ошибка получения истории мероприятий. Обратитесь в /support.", f"Ошибка БД при получении заявок пользователя {tg_id}: {e}"

    except Exception as e:
        return False, [], f"❌ Ошибка получения истории мероприятий. Обратитесь в /support.", f"Неожиданная ошибка БД при получении заявок: {e}"
    

@connection
async def db_get_all_user_tg_ids(session) -> Tuple[bool, list[int], Optional[str]]:
    """
    Возвращает список всех tg_id пользователей из базы данных
    """

    try:
        stmt = select(Users.tg_id) 
        
        result = await session.execute(stmt)
        tg_ids = result.scalars().all()
        all_ids = [str(id) for id in tg_ids]
        
        return True, list(all_ids), f"Всего пользователей в БД: {len(all_ids)}", "✅ Успешно"  

    except SQLAlchemyError as e:
        return False, [], f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.", f"Ошибка БД при получении всех tg_id: {e}"
    
    except Exception as e:
        return False, [], f"❌ Ошибка базы данных. Обратитесь к разработчику с данной проблемой.",  f"Неожиданная ошибка БД: {e}"
    
@connection
async def db_update_user(
    session,
    tg_id_str: str,
    moderator_username: str
) -> Optional[Tuple[bool, str, Optional[int], Optional[str]]]:
    try:
        tg_id = int(tg_id_str)

        # Используем update() как в db_approve_application
        result = await session.execute(
            update(Users)
            .where(Users.tg_id == tg_id)
            .values(
                moderator_username=moderator_username,
                approval_date=datetime.now()
            )
            .returning(Users.id)
        )
        
        user_id = result.scalar_one_or_none()
        if not user_id:
            return False, f"Пользователь с tg_id {tg_id} не найден", None, None

        await session.commit()
        return True, f"Данные пользователя {tg_id} успешно обновлены", user_id, "✅ Успешно"

    except SQLAlchemyError as e:
        await session.rollback()
        return False, f"❌ Ошибка базы данных.", None, f"Ошибка БД: {str(e)}"

# Функция 2: Уменьшение количества товара на 1
@connection
async def db_decrease_reward_count(session, reward_id: int) -> tuple[bool, int | None, str | None]:
    """
    Уменьшает количество товара на 1
    Возвращает: (успех, новое_количество, название_товара)
    """
    try:
        reward = await session.get(Catalog_of_reward, reward_id)
        
        if not reward:
            return False, None, None
            
        if reward.count <= 0:
            return False, 0, reward.name_of_reward
            
        reward.count -= 1
        await session.flush()
        
        return True, reward.count, "✅ Успешно"
        
    except Exception as e:
        return False, f"❌ Ошибка базы данных. Пожалуйста, обратитесь в /support.", f"Ошибка БД при уменьшении количества товара {reward_id}: {str(e)}"


# Функция 3: Создание записи о выдаче
@connection
async def db_create_issuance_record(
    session,
    tg_id: int,
    username: str,
    reward_id: int,
    reward_name: str,
    price: float
) -> int | None:
    """
    Создает запись в таблице выдачи поощрений
    Возвращает: ID созданной записи или None
    """
    try:

        issuance = Issuance_of_rewards(
            tg_id=int(tg_id),
            username=username or str(tg_id),
            reward_id=reward_id,
            name_of_reward=reward_name,
            price=int(price),
            order_date=datetime.now(),
            status="Ожидает выдачи",
            moderator_username="Не указан"
        )
        
        session.add(issuance)
        await session.flush()
        
        return issuance.id, "✅ Успешно", "✅ Успешно"
        
    except Exception as e:
        return None, f"❌ Ошибка базы данных. Пожалуйста, обратитесь в /support.", f"Ошибка БД при создании записи о выдаче для пользователя {tg_id}: {str(e)}"
    
@connection
async def db_approve_issuance(
    session,
    issuance_id: int,
    moderator_username: str
) -> Tuple[bool, str, Optional[str]]:
    """
    Принятие заявки на выдачу поощрения
    - Меняет статус заявки на "Выдано"
    - Записывает moderator_username в заявку
    """
    try:
        issuance_result = await session.execute(
            select(Issuance_of_rewards).where(Issuance_of_rewards.id == issuance_id)
        )
        issuance = issuance_result.scalar_one_or_none()

        if not issuance:
            return False, f"❌ Заявка с ID {issuance_id} не найдена.", None

        if issuance.status != "Ожидает выдачи":
            return False, (f"❌ Заявка #{issuance_id} уже обработана. ", None)

        issuance.status = "Выдано"
        issuance.moderator_username = moderator_username

        await session.commit()

        return True, f"Заявка #{issuance_id} на выдачу поощрения подтверждена модератором {moderator_username}. Пользователь {issuance.tg_id}", "✅ Успешно"

    except SQLAlchemyError as e:
        await session.rollback()
        return False, "❌ Ошибка базы данных. Обратитесь в /support.", f"Ошибка БД при подтверждении заявки #{issuance_id}: {str(e)}"
    
    except Exception as e:
        await session.rollback()
        return False, "❌ Ошибка базы данных. Обратитесь в /support.", f"Неожиданная ошибка БД при подтверждении заявки #{issuance_id}: {str(e)}"