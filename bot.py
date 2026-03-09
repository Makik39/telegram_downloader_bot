import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import config
from downloader import VideoDownloader
from database import Database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

downloader = VideoDownloader()
db = Database()

# 👇 Функция для отправки уведомления о реферале
async def send_referral_notification(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    referrer_id = job.data['referrer_id']
    user_id = job.data['user_id']
    
    try:
        await context.bot.send_message(
            chat_id=referrer_id,
            text=f"🎉 **У тебя новый реферал!**\n\nПользователь с ID `{user_id}` присоединился по твоей ссылке.\n✅ Ты получил **+5 попыток**!",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Не удалось отправить уведомление: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "no_username"
    first_name = user.first_name
    
    args = context.args
    referred_by = int(args[0]) if args and args[0].isdigit() else None
    if referred_by == user_id:
        referred_by = None
    
    # 👇 Если это реферальный переход, планируем уведомление
    if referred_by:
        context.job_queue.run_once(
            send_referral_notification, 
            2,  # через 2 секунды
            data={'referrer_id': referred_by, 'user_id': user_id}
        )
    
    db.add_user(user_id, username, first_name, referred_by)
    
    link = db.get_referral_link(user_id) or f"https://t.me/{config.BOT_USERNAME}?start={user_id}"
    ref_count = db.get_referral_count(user_id)
    attempts = db.get_attempts(user_id)
    
    # 👇 ОБНОВЛЁННЫЙ ТЕКСТ С ИНФОРМАЦИЕЙ О БОНУСАХ
    text = f"""
👋 Привет, {first_name}!

🎮 У тебя **{attempts} попыток** скачивания
💰 **+5 попыток** за каждого приглашённого друга!

🔗 Твоя реферальная ссылка:
{link}

⚡️ Сделано при поддержке Егора Горбасева
    """
    
    # 👇 ДОБАВЛЕНА КНОПКА "ИНФОРМАЦИЯ"
    keyboard = [
        [InlineKeyboardButton("👥 Мои рефералы", callback_data="refs")],
        [InlineKeyboardButton("🔗 Моя ссылка", callback_data="mylink")],
        [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    
    if q.data == "refs":
        refs = db.get_referral_details(user_id)
        if refs:
            text = "👥 Твои рефералы:\n"
            for i, ref in enumerate(refs, 1):
                text += f"{i}. {ref[2]} (@{ref[1]})\n"
        else:
            text = "👥 Пока нет рефералов"
        
        text += "\n\n⚡️ Сделано при поддержке Егора Горбасева"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back")]]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif q.data == "mylink":
        link = db.get_referral_link(user_id) or f"https://t.me/{config.BOT_USERNAME}?start={user_id}"
        count = db.get_referral_count(user_id)
        text = f"🔗 Твоя ссылка:\n{link}\n\n👥 Приглашено: {count}\n\n⚡️ Сделано при поддержке Егора Горбасева"
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back")]]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    # 👇 НОВАЯ КНОПКА "ИНФОРМАЦИЯ"
    elif q.data == "info":
        info_text = """
ℹ️ **ИНФОРМАЦИЯ О БОТЕ**

🎥 **Какие видео можно скачивать:**
• **YouTube** (любые видео и shorts)
• **TikTok** (без водяных знаков)

📦 **Ограничения:**
• Максимальный размер: 500 МБ
• Поддерживаются форматы MP4 и MP3

🎮 **Система попыток:**
• При первом запуске даётся **3 попытки**
• Пригласи друга → **+5 попыток**
• Сыграй в игру → **+3 попытки** (раз в 5 дней)

⚡️ Сделано при поддержке Егора Горбасева
"""
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back")]]
        await q.edit_message_text(info_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif q.data == "back":
        user = update.effective_user
        ref_count = db.get_referral_count(user_id)
        attempts = db.get_attempts(user_id)
        link = db.get_referral_link(user_id) or f"https://t.me/{config.BOT_USERNAME}?start={user_id}"
        
        text = f"""
👋 Привет, {user.first_name}!

🎮 У тебя **{attempts} попыток** скачивания
💰 **+5 попыток** за каждого приглашённого друга!

🔗 Твоя реферальная ссылка:
{link}

⚡️ Сделано при поддержке Егора Горбасева
        """
        keyboard = [
            [InlineKeyboardButton("👥 Мои рефералы", callback_data="refs")],
            [InlineKeyboardButton("🔗 Моя ссылка", callback_data="mylink")],
            [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    if db.get_attempts(user_id) <= 0:
        await update.message.reply_text("❌ Нет попыток. Пригласи друга!")
        return
    
    msg = await update.message.reply_text("⏳ Скачиваю...")
    
    try:
        db.use_attempt(user_id)
        path = await downloader.download_video(url)
        
        if not path:
            db.add_attempts(user_id, 1, "возврат")
            await msg.edit_text("❌ Не удалось скачать")
            return
        
        with open(path, 'rb') as f:
            await update.message.reply_video(f, caption=f"✅ Готово!\n\n⚡️ Сделано при поддержке Егора Горбасева")
        os.remove(path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)[:50]}")
        db.add_attempts(user_id, 1, "возврат")

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()