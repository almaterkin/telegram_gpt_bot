import os
import openai
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import logging

nest_asyncio.apply()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Переменные среды
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Должно содержать /telegram на конце

# OpenAI API
openai.api_key = OPENAI_API_KEY

PROMPTS = {
    "ru": {
        "role": "system",
        "content": (
            "‼️ Всегда строго отвечай на языке последнего сообщения пользователя. Никогда не меняй язык самостоятельно.\n\n"
            "Ты — профессиональный правовой консультант, специализирующийся на законодательстве Республики Казахстан..."
            # ... остальной текст
        )
    },
    "kz": {
        "role": "system",
        "content": (
            "‼️ Әрқашан пайдаланушының соңғы хабарламасының тілінде қатаң жауап бер..."
            # ... остальной текст
        )
    }
}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        logger.warning("No effective_message in /start")
        return
    logger.info(f"/start from user: {message.from_user.id}")
    keyboard = [
        [InlineKeyboardButton("Қазақ тілі", callback_data="kz")],
        [InlineKeyboardButton("Русский язык", callback_data="ru")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Тілді таңдаңыз / Выберите язык:", reply_markup=reply_markup)

# Выбор языка
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data["lang"] = lang

    greeting = {
        "ru": "Здравствуйте! Я ваш правовой консультант. Задавайте вопросы!",
        "kz": "Сәлеметсіз бе! Мен сіздің құқықтық кеңесшіңізбін. Сұрақтарыңызды қойыңыз!"
    }
    await query.edit_message_text(text=greeting[lang])

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = context.user_data.get("lang")

    if not lang:
        await update.message.reply_text("⛔ Сначала выберите язык с помощью команды /start")
        return

    logger.info(f"Message from {update.message.from_user.id}: {user_message}")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[PROMPTS[lang], {"role": "user", "content": user_message}]
        )
        reply = response["choices"][0]["message"]["content"]
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        await update.message.reply_text("⚠️ Қате орын алды / Произошла ошибка. Попробуйте позже.")

# Запуск
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if WEBHOOK_URL:
        await app.bot.set_webhook(WEBHOOK_URL)
        await app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 5000)),
            webhook_url=WEBHOOK_URL,
            path="/telegram"  # ВАЖНО: путь должен совпадать с тем, что в WEBHOOK_URL
        )
    else:
        logger.error("❌ WEBHOOK_URL не установлен!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
