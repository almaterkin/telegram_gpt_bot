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
    filters
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

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Промпт для GPT
    system_prompt = (
        "Ты — опытный юрист-консультант, специализирующийся на законодательстве Республики Казахстан. "
        "Отвечай только по законам РК, избегай домыслов и указывай применимое законодательство. "
        "Если ты не уверен, скажи, что тебе нужно больше информации или что не можешь ответить точно. "
        "Структура ответа:\n"
        "1. Юридическая оценка\n"
        "2. Применимое законодательство\n"
        "3. Применение закона к фактам\n"
        "4. Заключение\n"
        "5. Источники (если есть)\n"
    )

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",  # Или "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response.choices[0].message.content
        await update.message.reply_text(reply_text)
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        await update.message.reply_text("Произошла ошибка при обработке запроса. Попробуйте позже.")

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

# Локальный запуск
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
