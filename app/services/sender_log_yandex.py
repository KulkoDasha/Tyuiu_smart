import os
import smtplib
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, make_msgid
from ..config import *
from .logger import bot_logger

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

# ОТПРАВКА ПИСЬМА

def send_log_file():
    """Отправка логов"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    bot_logger.log_admin_msg(
        tg_id="Отправка логов", 
        message=f"🚀 ЗАПУСК ОТПРАВКИ\n"
               f"📁 Рабочая директория: {os.getcwd()}\n"
               f"⏰ Время: {timestamp}"
    )
    
    try:
        existing_files = []
        for name, path in LOG_FILES.items():
            # ← Лог проверки каждого файла
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
        
        # Создание сообщения
        msg = MIMEMultipart('mixed')
        msg['From'] = formataddr((str(Header('ТИУмничка', 'utf-8')), SENDER_EMAIL))
        msg['To'] = formataddr((str(Header('Администратор', 'utf-8')), RECIPIENT_EMAIL))
        msg['Subject'] = Header(f'📋 Логи Telegram-бота "ТИУмничка" за {datetime.now().strftime("%d.%m.%Y %H:%M")}', 'utf-8')
        msg['Reply-To'] = SENDER_EMAIL
        msg['Date'] = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = make_msgid(domain='yandex.ru')
        msg['X-Mailer'] = 'Python-LogSender/1.0'
        
        # Тело письма
        body_plain = f"""Автоматическая отправка логов Telegram-бота
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Время: {timestamp}
Файлов: {len(existing_files)}

Список файлов:
"""
        for name, _, size in existing_files:
            body_plain += f"  • {name} ({size} байт)\n"
        
        body_plain += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        body_plain += f"Отправитель: {SENDER_EMAIL}\n"
        body_plain += f"Получатель: {RECIPIENT_EMAIL}\n"
        
        msg.attach(MIMEText(body_plain, 'plain', 'utf-8'))
        
        # # Прикрепление файлов
        # for file_name, file_path, file_size in existing_files:
        #     try:
        #         with open(file_path, 'rb') as f:
        #             part = MIMEBase('application', 'octet-stream')
        #             part.set_payload(f.read())
        #             encoders.encode_base64(part)
                    
        #             ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        #             safe_name = file_name.replace('.log', '')
        #             attachment_name = f"{safe_name}_{ts}.log"
                    
        #             part.add_header('Content-Disposition', 'attachment', filename=attachment_name)
        #             msg.attach(part)
        #     except IOError as e:
        #         bot_logger.log_admin_msg(tg_id = "Отправка логов", message=f"Ошибка чтения {file_path}: {e}")
        
        # Подключение к SMTP
        bot_logger.log_admin_msg(tg_id = "Отправка логов", message=f"📨 Подключение к {SMTP_SERVER}:{SMTP_PORT}...")
    
        server = None
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            result = server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
            if result:
                # Сервер вернул ошибки по получателям
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
        bot_logger.log_admin_msg(tg_id = "Отправка логов", message=f"❌ Ошибка авторизации: {e}")
        bot_logger.log_admin_msg(tg_id = "Отправка логов", message="💡 Проверьте пароль приложения Яндекс")
        return False
    except Exception as e:
        bot_logger.log_admin_msg(tg_id = "Отправка логов", message=f"❌ Ошибка: {type(e).__name__}: {e}")
        return False