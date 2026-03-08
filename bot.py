import logging
import os
import subprocess
import sys

# Принудительная установка aiohttp, если её нет
try:
    import aiohttp
except ImportError:
    print("⚠️ aiohttp не найден, устанавливаю...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "aiohttp"])
    import aiohttp
    print("✅ aiohttp успешно установлен")

import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# ... остальные импорты
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import config
from downloader import VideoDownloader
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация загрузчика и базы данных
downloader = VideoDownloader()
db = Database()

# Команда /start с поддержкой рефералок
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "нет_username"
    first_name = user.first_name
    
    print(f"\n🔍 НОВЫЙ ЗАПУСК /start от пользователя {user_id}")
    
    # Проверяем, есть ли реферальный параметр
    args = context.args
    referred_by = None
    
    if args:
        try:
            referred_by = int(args[0])
            print(f"   📌 Переход по реферальной ссылке от {referred_by}")
            # Не даем бонус, если пользователь пригласил сам себя
            if referred_by == user_id:
                print("   ⚠️ Пользователь попытался пригласить сам себя")
                referred_by = None
        except ValueError:
            print(f"   ⚠️ Некорректный реферальный параметр: {args[0]}")
            referred_by = None
    
    # Добавляем пользователя в базу данных
    db.add_user(user_id, username, first_name, referred_by)
    
    # Получаем данные пользователя
    referral_link = db.get_referral_link(user_id) or f"https://t.me/{config.BOT_USERNAME}?start={user_id}"
    referral_count = db.get_referral_count(user_id)
    attempts = db.get_attempts(user_id)
    total_earned = db.get_total_earned_attempts(user_id)
    
    print(f"   📊 Статистика пользователя {user_id}:")
    print(f"      Попытки: {attempts}")
    print(f"      Рефералов: {referral_count}")
    
    welcome_text = f"""
👋 Привет, {first_name}!

Я бот для скачивания видео из TikTok и YouTube без водяных знаков.

🎮 <b>СИСТЕМА ПОПЫТОК:</b>
• У тебя есть <b>{attempts}</b> попыток скачивания
• Всего заработано: {total_earned} попыток
• За каждого приглашенного друга ты получаешь +5 попыток!

🔹 Просто отправь мне ссылку на видео
🔹 Поддерживаются: TikTok, YouTube, YouTube Shorts

📊 Твоя статистика:
• Приглашено друзей: {referral_count}
• Твоя реферальная ссылка: <a href="{referral_link}">{referral_link}</a>

⚠️ Максимальный размер файла: {config.MAX_FILE_SIZE // (1024*1024)} MB
⚡️ Быстро и бесплатно!
    """
    
    # Создаем клавиатуру с кнопками
    keyboard = [
        [InlineKeyboardButton(f"🎮 Попытки: {attempts}", callback_data="my_attempts")],
        [InlineKeyboardButton("🔗 Моя реферальная ссылка", callback_data="my_referral")],
        [InlineKeyboardButton("👥 Мои рефералы", callback_data="my_referrals")],
        [InlineKeyboardButton("🏆 Топ рефереров", callback_data="top_referrers")],
        [InlineKeyboardButton("📊 Моя статистика", callback_data="my_stats")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

# Обработка callback-кнопок
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    print(f"\n🔘 НАЖАТА КНОПКА: {query.data} от пользователя {user_id}")
    
    if query.data == "my_attempts":
        attempts = db.get_attempts(user_id)
        total_earned = db.get_total_earned_attempts(user_id)
        history = db.get_attempts_history(user_id, 5)
        
        text = f"""
🎮 <b>СИСТЕМА ПОПЫТОК</b>

📊 Текущие попытки: <b>{attempts}</b>
🏆 Всего заработано: {total_earned}

<b>Как получить попытки:</b>
• Пригласи друга - получи +5 попыток
• Каждое скачивание - 1 попытка

<b>Последние действия:</b>
"""
        
        if history:
            for change, reason, date, remaining in history:
                emoji = "➕" if change > 0 else "➖"
                date_str = date.split()[1][:5]  # Только время
                text += f"\n{emoji} {reason}: {abs(change)} ({remaining} осталось) - {date_str}"
        else:
            text += "\nПока нет истории действий"
        
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "my_referral":
        referral_link = db.get_referral_link(user_id) or f"https://t.me/{config.BOT_USERNAME}?start={user_id}"
        referral_count = db.get_referral_count(user_id)
        
        print(f"   📋 Запрос реферальной ссылки для {user_id}")
        print(f"      Ссылка: {referral_link}")
        print(f"      Рефералов: {referral_count}")
        
        # Делаем ссылку кликабельной
        text = f"""
🔗 <b>Твоя реферальная ссылка:</b>

<a href="{referral_link}">{referral_link}</a>

📊 Приглашено друзей: {referral_count}
💰 Получено попыток: {referral_count * 5}

💡 <b>Как это работает:</b>
1. Нажми на ссылку выше или отправь её друзьям
2. Когда друг перейдет по ссылке и запустит бота, ты получишь +5 попыток
3. Приглашай больше друзей и качай больше видео!
        """
        
        # Кнопка для копирования ссылки
        keyboard = [
            [InlineKeyboardButton("📋 Скопировать ссылку", callback_data="copy_link")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "my_referrals":
        print(f"   👥 Запрос списка рефералов для {user_id}")
        
        referrals = db.get_referral_details(user_id)
        attempts = db.get_attempts(user_id)
        
        print(f"      Найдено рефералов: {len(referrals) if referrals else 0}")
        
        if referrals:
            text = f"👥 <b>Твои приглашенные друзья:</b>\nТвои попытки: {attempts}\n\n"
            for i, ref in enumerate(referrals, 1):
                # Распаковываем данные реферала
                user_id_ref, username, first_name, join_date, downloads, bonus = ref
                username_text = f"@{username}" if username and username != "нет_username" else first_name
                date = join_date.split()[0] if join_date else "неизвестно"
                text += f"{i}. {username_text}\n"
                text += f"   📅 Присоединился: {date}\n"
                text += f"   📥 Скачиваний: {downloads}\n"
                text += f"   💰 Ты получил: +{bonus} попыток\n\n"
        else:
            text = f"👥 У тебя пока нет приглашенных друзей.\n\nТвои попытки: {attempts}\n\nПригласи друзей по своей реферальной ссылке и получи +5 попыток за каждого!"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "top_referrers":
        top_users = db.get_top_referrers(10)
        user_attempts = db.get_attempts(user_id)
        
        text = f"🏆 <b>Топ 10 рефереров:</b>\nТвои попытки: {user_attempts}\n\n"
        
        if top_users:
            for i, (user_id_top, username, first_name, count, total_earned) in enumerate(top_users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
                name = f"@{username}" if username and username != "нет_username" else first_name
                text += f"{medal} {i}. {name}\n"
                text += f"   👥 Рефералов: {count}\n"
                text += f"   💰 Всего попыток: {total_earned}\n\n"
        else:
            text += "Пока нет данных. Будь первым!"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "my_stats":
        stats = db.get_user_stats(user_id)
        referral_count = db.get_referral_count(user_id)
        
        if stats:
            total, tiktok, youtube, attempts, total_earned = stats
            text = f"""
📊 <b>Твоя статистика:</b>

🎮 Попытки: <b>{attempts}</b> (всего заработано: {total_earned})
🎬 Всего скачиваний: {total}
📱 TikTok: {tiktok}
▶️ YouTube: {youtube}
👥 Приглашено друзей: {referral_count}
💰 Попыток от рефералов: {referral_count * 5}

📅 В боте с: {db.get_user_join_date(user_id)}
            """
        else:
            text = "📊 Статистика пока пуста"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "help":
        attempts = db.get_attempts(user_id)
        help_text = f"""
📚 <b>Как пользоваться ботом:</b>

1️⃣ Найди видео в TikTok или YouTube
2️⃣ Скопируй ссылку на видео
3️⃣ Отправь ссылку мне (1 попытка = 1 видео)
4️⃣ Получи видео без водяных знаков!

🎮 <b>Система попыток:</b>
• У тебя сейчас: {attempts} попыток
• Каждое скачивание = -1 попытка
• Новые пользователи получают 3 попытки

🎁 <b>Реферальная программа:</b>
• Пригласи друга = +5 попыток
• Друг тоже получает 3 попытки
• Соревнуйся в топе рефереров

📦 <b>Максимальный размер:</b> {config.MAX_FILE_SIZE // (1024*1024)} MB

❓ <b>Частые проблемы:</b>
• Если видео не скачивается - проверь доступ к видео
• Для приватных аккаунтов скачивание недоступно
        """
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "back_to_menu":
        # Возвращаемся в главное меню
        user = update.effective_user
        referral_count = db.get_referral_count(user_id)
        attempts = db.get_attempts(user_id)
        
        text = f"""
👋 Привет, {user.first_name}!

🎮 Твои попытки: <b>{attempts}</b>
👥 Рефералов: {referral_count}

Выбери действие из меню ниже:
        """
        
        keyboard = [
            [InlineKeyboardButton(f"🎮 Попытки: {attempts}", callback_data="my_attempts")],
            [InlineKeyboardButton("🔗 Моя реферальная ссылка", callback_data="my_referral")],
            [InlineKeyboardButton("👥 Мои рефералы", callback_data="my_referrals")],
            [InlineKeyboardButton("🏆 Топ рефереров", callback_data="top_referrers")],
            [InlineKeyboardButton("📊 Моя статистика", callback_data="my_stats")],
            [InlineKeyboardButton("🆘 Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "copy_link":
        await query.answer("Ссылка скопирована! Отправь её друзьям.", show_alert=True)

# Функция проверки поддерживаемого URL
def is_supported_url(url: str) -> tuple:
    url_lower = url.lower()
    for domain, platform in config.SUPPORTED_SITES.items():
        if domain in url_lower:
            return True, platform
    return False, None

# ========== ИСПРАВЛЕННАЯ ФУНКЦИЯ ОБРАБОТКИ СООБЩЕНИЙ ==========
# (ТОЛЬКО ОДНА, БЕЗ ДУБЛИКАТОВ)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    print(f"\n📨 ПОЛУЧЕНА ССЫЛКА от {user_id}: {url[:50]}...")
    
    # Проверяем, поддерживается ли ссылка
    is_supported, platform = is_supported_url(url)
    
    if not is_supported:
        await update.message.reply_text(
            "❌ Неподдерживаемая ссылка.\n"
            "Пожалуйста, отправьте ссылку на TikTok или YouTube."
        )
        return
    
    # Проверяем наличие попыток ДО скачивания
    attempts_before = db.get_attempts(user_id)
    print(f"   🎮 Попыток до скачивания: {attempts_before}")
    
    if attempts_before <= 0:
        keyboard = [
            [InlineKeyboardButton("🔗 Пригласить друзей", callback_data="my_referral")],
            [InlineKeyboardButton("🎮 Мои попытки", callback_data="my_attempts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ У тебя закончились попытки скачивания!\n\n"
            "Пригласи друзей по реферальной ссылке и получи +5 попыток за каждого!",
            reply_markup=reply_markup
        )
        return
    
    # Отправляем сообщение о начале обработки
    status_message = await update.message.reply_text(
        f"⏳ Обрабатываю ссылку с {platform}...\n"
        f"🎮 Осталось попыток: {attempts_before}\n"
        "Это может занять несколько секунд"
    )
    
    # Переменная для отслеживания успешности
    download_successful = False
    attempt_used = False
    
    try:
        # Скачиваем видео (попытка НЕ списывается, если не удалось)
        filepath = await downloader.download_video(url)
        
        if not filepath or not os.path.exists(filepath):
            await status_message.edit_text(
                "❌ Не удалось скачать видео. Попробуйте другую ссылку.\n"
                f"🎮 Попытки не потрачены: {attempts_before}"
            )
            return
        
        # Проверяем размер скачанного файла
        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"📊 Размер видео: {file_size_mb:.2f} МБ")
        
        if file_size > config.MAX_FILE_SIZE:
            await status_message.edit_text(
                f"❌ Файл слишком большой ({file_size_mb:.1f} МБ)\n"
                f"Максимальный размер: {config.MAX_FILE_SIZE // (1024*1024)} МБ\n"
                f"🎮 Попытки не потрачены: {attempts_before}"
            )
            downloader.cleanup(filepath)
            return
        
        # ✅ ТОЛЬКО ЗДЕСЬ списываем попытку - видео скачано и готово к отправке
        db.use_attempt(user_id)
        attempt_used = True
        attempts_after = attempts_before - 1
        print(f"   ✅ Попытка списана. Осталось: {attempts_after}")
        
        # Отправляем видео с увеличенными таймаутами
        await status_message.edit_text(
            f"📤 Отправляю видео...\n"
            f"📦 Размер: {file_size_mb:.1f} МБ\n"
            f"🎮 Осталось попыток: {attempts_after}\n"
            f"⏳ Это может занять несколько минут..."
        )
        
        try:
            with open(filepath, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"✅ Скачано с {platform}\n\n"
                            f"👤 Запросил: @{username}\n"
                            f"🤖 @{config.BOT_USERNAME}\n"
                            f"🎮 Осталось попыток: {attempts_after}\n"
                            f"📦 Размер: {file_size_mb:.1f} МБ",
                    supports_streaming=True,
                    read_timeout=600,
                    write_timeout=600,
                )
            print(f"✅ Видео успешно отправлено")
            download_successful = True
            
        except Exception as e:
            print(f"❌ Ошибка при отправке видео: {e}")
            await status_message.edit_text(
                f"❌ Не удалось отправить видео.\n"
                f"🎮 Попытки восстановлены: {attempts_before}\n"
                f"Ошибка: {str(e)[:100]}"
            )
            # Возвращаем попытку, так как отправка не удалась
            db.add_attempts(user_id, 1, "Возврат попытки (ошибка отправки)")
            downloader.cleanup(filepath)
            return
        
        # Удаляем временный файл
        downloader.cleanup(filepath)
        
        # Обновляем статистику в базе данных
        platform_db = 'tiktok' if 'tiktok' in url.lower() else 'youtube'
        db.update_download_stats(user_id, platform_db)
        
        # Удаляем статусное сообщение
        await status_message.delete()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {e}", exc_info=True)
        
        # Проверяем, не была ли уже списана попытка
        current_attempts = db.get_attempts(user_id)
        
        error_text = f"❌ Произошла ошибка при скачивании.\n"
        
        if attempt_used:
            # Если попытка была списана, но видео не скачано, возвращаем её
            db.add_attempts(user_id, 1, "Возврат попытки (ошибка скачивания)")
            error_text += f"🎮 Попытка возвращена. Текущие попытки: {current_attempts + 1}\n"
        else:
            error_text += f"🎮 Попытки не потрачены: {current_attempts}\n"
        
        error_text += f"Попробуйте другую ссылку или повторите позже."
        
        await status_message.edit_text(error_text)

def main():
    """Запуск бота"""
    
    # Проверяем наличие токена
    if not config.BOT_TOKEN or config.BOT_TOKEN == "ВАШ_ТОКЕН_СЮДА":
        print("❌ Ошибка: Не указан токен бота!")
        print("Получите токен у @BotFather и добавьте его в .env файл")
        return
    
    # Создаем приложение
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Добавляем обработчик callback-кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("✅ Бот с реферальной системой запущен!")
    print(f"🤖 @{config.BOT_USERNAME}")
    print("📊 База данных с системой попыток инициализирована")
    print("🔍 Включен режим отладки - смотрите вывод в консоли")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()