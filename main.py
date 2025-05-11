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
    MessageHandler,
    ContextTypes,
    filters,
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

# ✅ Обработка текстовых сообщений с отправкой запроса в OpenAI
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты — юридический консультант, отвечай строго по законам Казахстана, кратко и по делу."},
                {"role": "user", "content": user_message}
            ]
        )
        answer = response["choices"][0]["message"]["content"]
        await context.bot.send_message(chat_id=chat_id, text=answer)

    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        await context.bot.send_message(chat_id=chat_id, text="Произошла ошибка при обращении к ИИ. Попробуйте позже.")

# Регистрируем обработку обычных сообщений
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# FastAPI
app = FastAPI()

@app.on_event("startup")
async def startup():
    await bot_app.initialize()
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
