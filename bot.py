from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from datetime import datetime, timedelta
import json
import os
import random
import string

# === НАСТРОЙКИ ===
BOT_TOKEN = "8061219020:AAGJQigQsRiVEQujQkzmDnyBrJiHcwB-Gp0"
CHANNEL_USERNAME = "@psyho_bomb"
ADMIN_IDS = [6872143002]

CODES_FILE = "codes.json"
USED_CODES_FILE = "used_codes.json"

# === УТИЛИТЫ ===
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_code(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def is_user_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton("✅ Получить код", callback_data="get_code")]
    ])
    await update.message.reply_text("👋 Привет! Подпишись на канал и получи код:", reply_markup=keyboard)

# === КНОПКИ ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "get_code":
        if not await is_user_subscribed(user_id, context):
            await query.edit_message_text("❌ Сначала подпишитесь на канал.")
            return

        now = datetime.now()
        used = load_json(USED_CODES_FILE)
        last_time = used.get(str(user_id))

        if last_time:
            last_time_dt = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
            if last_time_dt + timedelta(hours=24) > now:
                wait = last_time_dt + timedelta(hours=24) - now
                await query.edit_message_text(f"⏳ Получить новый код можно через: {str(wait).split('.')[0]}")
                return

        code = generate_code()
        expire_time = (now + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')

        codes = load_json(CODES_FILE)
        codes[code] = expire_time
        save_json(CODES_FILE, codes)

        used[str(user_id)] = now.strftime('%Y-%m-%d %H:%M:%S')
        save_json(USED_CODES_FILE, used)

        await query.edit_message_text(
            f"✅ Ваш код: `{code}`\n🕒 Действует до: {expire_time}",
            parse_mode="Markdown"
        )

# === /gen <дней> — команда для админа
async def gen_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав.")
        return

    try:
        days = int(context.args[0])
    except:
        await update.message.reply_text("⚠️ Использование: /gen <дней>")
        return

    code = generate_code()
    expire_time = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    codes = load_json(CODES_FILE)
    codes[code] = expire_time
    save_json(CODES_FILE, codes)

    await update.message.reply_text(
        f"✅ Сгенерирован код: `{code}`\n📅 Срок: {expire_time}",
        parse_mode="Markdown"
    )

# === ЗАПУСК ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("gen", gen_code))

    print("✅ Бот запущен.")
    app.run_polling()
