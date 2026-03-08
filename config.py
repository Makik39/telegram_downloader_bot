import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Токен бота (обязательно)
BOT_TOKEN = os.getenv('BOT_TOKEN', 'ВАШ_ТОКЕН_СЮДА')

# Поддерживаемые платформы
SUPPORTED_SITES = {
    'tiktok.com': 'TikTok',
    'vt.tiktok.com': 'TikTok',
    'youtube.com': 'YouTube',
    'youtu.be': 'YouTube',
    'youtube.com/shorts': 'YouTube',
}

# Настройки скачивания
DOWNLOAD_PATH = 'downloads'
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 МБ

# Настройки реферальной системы
REFERRAL_BONUS = 5
BOT_USERNAME = "Download12erBot"  # Ваш username бота (без @)