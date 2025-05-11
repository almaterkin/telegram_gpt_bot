import os
import openai
import nest_asyncio
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.ext.webhook import WebhookRequestHandler
import logging

nest_asyncio.apply()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY

# Языковые промты
PROMPTS = {
    "ru": {
        "role": "system",
        "content": (
            "‼️ Всегда строго отвечай на языке последнего сообщения пользователя..."
        )
    },
    "kz": {
        "role": "system",
        "content": (
            "‼️ Әрқашан пайдаланушының соңғы хабарламасының тілінде қатаң жауап бер..."
        )
    }
}

# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Қазақ тілі", callback_data="kz")],
        [InlineKeyboardButton("Русский язык", callback_data="ru")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Тілді таңдаңыз / Выберите язык:", reply_markup=reply_markup)

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = context.user_data.get("lang")
    if not lang:
        await update.message.reply_text("Сначала выберите язык с помощью /start")
        return
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[PROMPTS[lang], {"role": "user", "content": user_message}]
        )
        reply = response["choices"][0]["message"]["content"]
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("⚠️ Ошибка. Попробуйте позже.")

# FastAPI приложение
app = FastAPI()
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(choose_language))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook обработчик
@app.on_event("startup")
async def on_startup():
    await bot_app.bot.set_webhook(WEBHOOK_URL)

@app.post("/telegram")
async def telegram_webhook(request: Request):
    update = Update.de_json(await request.json(), bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}

