import os
import openai
import nest_asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import logging
import uvicorn

# Настроим обработку асинхронных событий
nest_asyncio.apply()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = os.getenv("PORT", 8000)  # Порт по умолчанию

openai.api_key = OPENAI_API_KEY

# Промт для GPT
PROMPT = {
    "ru": {
        "role": "system",
        "content": "‼️ Всегда строго отвечай на языке последнего сообщения пользователя..."
    },
    "kz": {
        "role": "system",
        "content": "‼️ Әрқашан пайдаланушының соңғы хабарламасының тілінде қатаң жауап бер..."
    }
}

# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Убираем выбор языка, сразу начинаем обработку
    greeting = {
        "ru": "Здравствуйте! Я ваш правовой консультант. Задавайте вопросы!",
        "kz": "Сәлеметсіз бе! Мен сіздің құқықтық кеңесшіңізбін. Сұрақтарыңызды қойыңыз!"
    }
    lang = "ru"  # По умолчанию русский
    await update.message.reply_text(greeting[lang])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = "ru"  # Установим язык, например, русский
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[PROMPT[lang], {"role": "user", "content": user_message}]
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
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.post("/telegram")
async def telegram_webhook(request: Request):
    update = Update.de_json(await request.json(), bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}

# Запуск приложения на правильном порту
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))
