import os
import logging
import openai
import uvicorn
import nest_asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

# Для работы asyncio внутри uvicorn
nest_asyncio.apply()

# Логирование
logging.basicConfig(level=logging.INFO)

# Переменные
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))

openai.api_key = OPENAI_API_KEY

# Telegram приложение
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ваш правовой консультант. Чем могу помочь?")

bot_app.add_handler(CommandHandler("start", start))

# FastAPI
app = FastAPI()

@app.on_event("startup")
async def startup():
    await bot_app.initialize()  # 🔧 ОБЯЗАТЕЛЬНО!
    await bot_app.bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Webhook установлен")

@app.on_event("shutdown")
async def shutdown():
    await bot_app.shutdown()

@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

# Локальный запуск (не нужен на Render)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
