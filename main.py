import os
import openai
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import nest_asyncio
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
PORT = os.getenv("PORT", 10000)  # Порт по умолчанию

openai.api_key = OPENAI_API_KEY

# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Отправить приветственное сообщение
    await update.message.reply_text("Привет! Я ваш правовой консультант. Чем могу помочь?")

# FastAPI приложение
app = FastAPI()

bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Установим обработчики
bot_app.add_handler(CommandHandler("start", start))

# Применяем Lifespan
@app.on_event("startup")
async def on_startup():
    await bot_app.bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.bot.delete_webhook()

@app.post("/telegram")
async def telegram_webhook(request: Request):
    # Получаем обновления от Telegram
    update = Update.de_json(await request.json(), bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}

# Запуск приложения с указанием порта
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))
