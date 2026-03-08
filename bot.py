import logging
import os
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

# Инициализация
downloader = VideoDownloader()
db = Database()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "нет_username"
    first_name = user.first_name

    args = context.args
    referred_by = None
    if args:
        try:
            referred_by = int(args[0])
            if referred_by == user_id:
                referred_by = None
        except:
            referred_by = None

    db.add_user(user_id, username, first_name, referred_by)

    referral_link = db.get_referral_link(user_id) or f"https://t.me/{config.BOT_USERNAME}?start={user_id}"
    referral_count = db.get_referral_count(user_id)
    attempts = db.get_attempts(user_id)

    welcome_text = f"""
👋 Привет, {first_name}!

🎮 Попыток: {attempts}
👥 Рефералов: {referral_count}

🔗 Твоя ссылка: <a href="{referral_link}">{referral_link}</a>
    """
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

# Команда для проверки рефералов (только для вас)
async def check_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_id = 7165406956  # Ваш ID

    if user_id != admin_id:
        await update.message.reply_text("⛔ Нет доступа")
        return

    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM referrals")
    refs = cursor.fetchall()

    text = "🔍 **РЕФЕРАЛЫ**\n\n"
    if refs:
        for r in refs:
            text += f"{r}\n"
    else:
        text += "Пусто\n"

    cursor.execute("SELECT user_id, first_name, referred_by FROM users WHERE referred_by IS NOT NULL")
    users = cursor.fetchall()
    text += "\n👥 **Приглашенные:**\n"
    if users:
        for u in users:
            text += f"{u[0]} ({u[1]}) -> {u[2]}\n"
    else:
        text += "Нет\n"

    await update.message.reply_text(text, parse_mode='Markdown')

# Заглушка для остальных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я пока только умею отвечать на /start и /checkref")

def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN == "ВАШ_ТОКЕН_СЮДА":
        print("❌ Нет токена в config.py")
        return

    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("checkref", check_referrals))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен (минимальная версия)")
    app.run_polling()

if __name__ == "__main__":
    main()