import os
import sys
import smtplib
import time
import zipfile
import tempfile
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr, make_msgid
from ..config import *
from .logger import bot_logger

# ==================== КОНФИГУРАЦИЯ ====================
SMTP_SERVER = 'smtp.yandex.ru'
SMTP_PORT = 587
SMTP_USE_TLS = True
SMTP_TIMEOUT = 30

LOG_FILES = {
    "AdminLog.log": "logs/AdminLog.log",
    "UserLog.log": "logs/UserLog.log",
    "ModeratorLog.log": "logs/ModeratorLog.log",
}

SEND_TIME = config.logs_send_time
SEND_ON_START = config.logs_send_on_start

SENDER_EMAIL = config.logs_sender_email
SENDER_PASSWORD = config.logs_sender_password
RECIPIENT_EMAIL = config.logs_recipient_email

# Настройки архива
MAX_ZIP_SIZE = 20 * 1024 * 1024  # 20 MB лимит


# ==================== ФУНКЦИИ ====================

def create_zip_archive(existing_files):
    """Создание ZIP-архива с лог-файлами"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_name = f"telegram_bot_logs_{timestamp}.zip"
    
    # Создаём временный файл
    temp_dir = tempfile.gettempdir()
    zip_path = os.path.join(temp_dir, archive_name)
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_name, file_path, file_size in existing_files:
                # Добавляем файл в архив с сохранением имени
                zipf.write(file_path, arcname=file_name)
                bot_logger.log_admin_msg(
                    tg_id="Отправка логов",
                    message=f"   📦 Добавлен в архив: {file_name} ({file_size} байт)"
                )
        
        zip_size = os.path.getsize(zip_path)
        bot_logger.log_admin_msg(
            tg_id="Отправка логов",
            message=f"   ✅ Архив создан: {archive_name} ({zip_size} байт)"
        )
        
        # Проверка размера
        if zip_size > MAX_ZIP_SIZE:
            bot_logger.log_admin_msg(
                tg_id="Отправка логов",
                message=f"   ⚠️  Размер архива превышает лимит ({MAX_ZIP_SIZE} байт)"
            )
        
        return zip_path, archive_name, zip_size
        
    except Exception as e:
        bot_logger.log_admin_msg(
            tg_id="Отправка логов",
            message=f"   ❌ Ошибка создания архива: {e}"
        )
        return None, None, 0


def send_log_file():
    """Отправка логов в ZIP-архиве"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    bot_logger.log_admin_msg(
        tg_id="Отправка логов", 
        message=f"🚀 ЗАПУСК ОТПРАВКИ ЛОГОВ\n"
               f"📁 Рабочая директория: {os.getcwd()}\n"
               f"⏰ Время: {timestamp}"
    )
    
    zip_path = None
    
    try:
        # 1. Проверка файлов
        existing_files = []
        for name, path in LOG_FILES.items():
            abs_path = os.path.abspath(path)
            exists = os.path.exists(abs_path)
            size = os.path.getsize(abs_path) if exists else 0
            
            bot_logger.log_admin_msg(
                tg_id="Отправка логов",
                message=f"📄 Файл: {name}\n"
                       f"   Путь: {abs_path}\n"
                       f"   Существует: {exists}\n"
                       f"   Размер: {size} байт"
            )
            
            if exists and size > 0:
                existing_files.append((name, abs_path, size))
        
        if not existing_files:
            bot_logger.log_admin_msg(
                tg_id="Отправка логов", 
                message="⚠️ НЕТ ФАЙЛОВ ДЛЯ ОТПРАВКИ (все пусты или не найдены)"
            )
            return False
        
        # 2. Создание ZIP-архива
        bot_logger.log_admin_msg(
            tg_id="Отправка логов",
            message=f"📦 Создание ZIP-архива ({len(existing_files)} файлов)..."
        )
        
        zip_path, archive_name, zip_size = create_zip_archive(existing_files)
        
        if not zip_path:
            bot_logger.log_admin_msg(
                tg_id="Отправка логов",
                message="❌ Не удалось создать архив"
            )
            return False
        
        # 3. Создание сообщения
        msg = MIMEMultipart('mixed')
        msg['From'] = formataddr((str(Header('ТИУмничка', 'utf-8')), SENDER_EMAIL))
        msg['To'] = formataddr((str(Header('Администратор', 'utf-8')), RECIPIENT_EMAIL))
        msg['Subject'] = Header(
            f'📋 Логи Telegram-бота "ТИУмничка" за {datetime.now().strftime("%d.%m.%Y %H:%M")}', 
            'utf-8'
        )
        msg['Reply-To'] = SENDER_EMAIL
        msg['Date'] = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = make_msgid(domain='yandex.ru')
        msg['X-Mailer'] = 'Python-LogSender/2.0 (ZIP)'
        
        # 4. Тело письма
        body_plain = f"""Автоматическая отправка логов Telegram-бота
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Время генерации: {timestamp}
Часовой пояс: {datetime.now().astimezone().tzname()}

📦 Архив с логами:
  • Имя: {archive_name}
  • Размер: {zip_size} байт
  • Файлов внутри: {len(existing_files)}

📄 Список файлов в архиве:
"""
        for name, _, size in existing_files:
            body_plain += f"  • {name} ({size} байт)\n"
        
        body_plain += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        body_plain += f"Отправитель: {SENDER_EMAIL}\n"
        body_plain += f"Получатель: {RECIPIENT_EMAIL}\n"
        body_plain += f"\n⚠️  Для распаковки используйте любой архиватор (7-Zip, WinRAR, etc.)\n"
        
        msg.attach(MIMEText(body_plain, 'plain', 'utf-8'))
        
        # 5. Прикрепление ZIP-архива
        bot_logger.log_admin_msg(
            tg_id="Отправка логов",
            message=f"📎 Прикрепление архива: {archive_name}"
        )
        
        with open(zip_path, 'rb') as f:
            part = MIMEBase('application', 'zip')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                'attachment',
                filename=archive_name
            )
            msg.attach(part)
        
        # 6. Подключение к SMTP и отправка
        bot_logger.log_admin_msg(
            tg_id="Отправка логов", 
            message=f"📨 Подключение к {SMTP_SERVER}:{SMTP_PORT}..."
        )
        
        server = None
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            
            result = server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
            
            if result:
                for recipient, error in result.items():
                    bot_logger.log_admin_msg(
                        tg_id="Отправка логов", 
                        message=f"❌ ОШИБКА ДОСТАВКИ для {recipient}: {error}"
                    )
                return False
            else:
                bot_logger.log_admin_msg(
                    tg_id="Отправка логов", 
                    message=f"✅ Письмо ПРИНЯТО сервером для доставки в {datetime.now().strftime('%H:%M:%S')}"
                )
                return True
                
        finally:
            if server:
                server.quit()
                time.sleep(2)
        
    except smtplib.SMTPAuthenticationError as e:
        bot_logger.log_admin_msg(
            tg_id="Отправка логов", 
            message=f"❌ Ошибка авторизации: {e}\n💡 Проверьте пароль приложения Яндекс"
        )
        return False
        
    except smtplib.SMTPRecipientsRefused as e:
        bot_logger.log_admin_msg(
            tg_id="Отправка логов", 
            message=f"❌ Получатель отклонён: {e}\n💡 Возможно превышен лимит отправки"
        )
        return False
        
    except Exception as e:
        bot_logger.log_admin_msg(
            tg_id="Отправка логов", 
            message=f"❌ Ошибка: {type(e).__name__}: {e}"
        )
        return False
        
    finally:
        # 7. Очистка временного файла
        if zip_path and os.path.exists(zip_path):
            try:
                os.remove(zip_path)
                bot_logger.log_admin_msg(
                    tg_id="Отправка логов",
                    message=f"🧹 Временный архив удалён: {zip_path}"
                )
            except Exception as e:
                bot_logger.log_admin_msg(
                    tg_id="Отправка логов",
                    message=f"⚠️  Не удалось удалить временный файл: {e}"
                )


# ==================== ПЛАНИРОВЩИК ====================

def run_scheduler():
    """Фоновый запуск планировщика"""
    import schedule
    
    bot_logger.log_admin_msg(
        tg_id="Отправка логов",
        message=f"⏰ Планировщик запущен. Отправка в {SEND_TIME} ежедневно"
    )
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            bot_logger.log_admin_msg(
                tg_id="Отправка логов",
                message="🛑 Планировщик остановлен пользователем"
            )
            break
        except Exception as e:
            bot_logger.log_admin_msg(
                tg_id="Отправка логов",
                message=f"❌ Ошибка планировщика: {e}"
            )
            time.sleep(60)

if __name__ == "__main__":
    import threading
    
    print("=" * 60)
    print("📦 ОТПРАВКА ЛОГОВ TELEGRAM-БОТА (ZIP)")
    print("=" * 60)
    
    # Настройка расписания
    import schedule
    schedule.every().day.at(SEND_TIME).do(send_log_file)
    
    # Запуск планировщика в потоке
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Тестовая отправка
    if SEND_ON_START:
        bot_logger.log_admin_msg(
            tg_id="Отправка логов",
            message="🧪 ТЕСТОВАЯ ОТПРАВКА ПРИ ЗАПУСКЕ"
        )
        send_log_file()
    
    # Основной цикл
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bot_logger.log_admin_msg(
            tg_id="Отправка логов",
            message="👋 Завершение работы..."
        )
        sys.exit(0)