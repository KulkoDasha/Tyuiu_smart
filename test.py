from environs import Env
from pathlib import Path

# Проверка пути
env_path = Path.cwd() / ".env"
print(f"Текущая директория: {Path.cwd()}")
print(f"Путь к .env: {env_path}")
print(f".env существует: {env_path.exists()}")

if env_path.exists():
    # Чтение файла напрямую
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print("\nСодержимое .env:")
        print(content)
    
    # Чтение через environs
    env = Env()
    env.read_env(env_path)
    
    token = env("BOT_TOKEN")
    print(f"\nПрочитанный BOT_TOKEN: {token}")
    print(f"Длина токена: {len(token)} символов")
    print(f"Начинается с: {token[:10]}...")
else:
    print("Файл .env не найден!")