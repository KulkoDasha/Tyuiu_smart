import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import time
import threading

def send_log_file():
    """Отправка лог-файла на почту"""
    try:
        
        log_files = {
            "AdminLog.log": "logs\\AdminLog.log",
            "UserLog.log": "logs\\UserLog.log", 
            "ModeratorLog.log": "logs\\ModeratorLog.log"
        }
        
        # Проверяем, существуют ли файлы
        existing_files = []
        for name, path in log_files.items():
            if os.path.exists(path):
                existing_files.append((name, path))
                print(f"Найден файл: {path}")
            else:
                print(f"Файл не найден: {path}")
        
        if not existing_files:
            print("Нет файлов для отправки")
            return
        
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = 'kulko.dasha.2006@gmail.com'
        msg['To'] = 'abramushkinan@std.tyuiu.ru'
        msg['Subject'] = f'Логи Telegram бота за {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        
        # Добавляем текст письма
        body = f"Логи бота за {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        body += f"Отправлено файлов: {len(existing_files)}\n"
        body += f"Файлы: {', '.join([f[0] for f in existing_files])}"
        msg.attach(MIMEText(body, 'plain'))
        
        for file_name, file_path in existing_files:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                
                # Формируем имя файла с датой
                attachment_name = f"{file_name.replace('.log', '')}_{datetime.now().strftime('%Y%m%d_%H%M')}.log"
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{attachment_name}"'
                )
                msg.attach(part)
                print(f"Прикреплён файл: {file_name}")
        
        # Отправляем письмо
        print("📨 Подключаюсь к почтовому серверу...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('kulko.dasha.2006@gmail.com', 'cbho pqqw csxe wxbg')  
        text = msg.as_string()
        server.sendmail('kulko.dasha.2006@gmail.com', 'abramushkinan@std.tyuiu.ru', text)
        server.quit()
        
        print(f"Логи успешно отправлены в {datetime.now()}")
        
    except Exception as e:
        print(f"Ошибка при отправке логов: {e}")

# Настройка расписания
#schedule.every().day.at("23:59").do(send_log_file)  # Каждый день в 23:59


# Запуск планировщика в фоне
"""def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)"""

"""# Запускаем планировщик в отдельном потоке
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()"""

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 ЗАПУСК ОТПРАВКИ ЛОГОВ")
    print("=" * 50)
    send_log_file()
    print("✅ Готово!")