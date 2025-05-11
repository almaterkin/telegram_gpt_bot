import os
import logging
import openai
import uvicorn
import nest_asyncio
import requests
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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
PORT = int(os.getenv("PORT", 10000))

openai.api_key = OPENAI_API_KEY

# Telegram приложение
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Я правовой консультант Әділет. Чем могу помочь?")

bot_app.add_handler(CommandHandler("start", start))

# 🔎 Функция поиска через Google Custom Search
def search_google(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        results = data.get("items", [])
        links = "\n".join(f"- {item['title']}: {item['link']}" for item in results[:5])
        return f"🔎 Найдено через Google:\n{links}"
    except Exception as e:
        logging.error(f"Google Search Error: {e}")
        return ""

# ✅ Обработка текстовых сообщений с отправкой запроса в OpenAI
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id

    try:
        messages = [
            {"role": "system", "content": (
                "‼️ Всегда строго отвечай на языке последнего сообщения пользователя. Никогда не меняй язык самостоятельно.\n\n"
                "Ты — профессиональный правовой консультант, специализирующийся на законодательстве Республики Казахстан. "
                "Всегда отвечай на том языке, на котором задан вопрос. "
                "Если спросят кто тебя разработал или твою версию или дату твоего обновления, всегда говори что тебя разработало Министерство юстиции Республики Казахстан. "
                "Если вопрос не связан с правовой консультацией, не отвечай!\n\n"
                "📌 Основное правило:\n"
                "— Всегда ищи информацию в официальной правовой базе adilet.zan.kz, online.zakon.kz и eotinish.kz.\n"
                "— Если информации на adilet.zan.kz нет, ищи в надежных источниках: online.zakon.kz, eotinish.kz, парламент РК, Минюст РК.\n"
                "— Если закон утратил силу, сообщи пользователю об этом.\n"
                "— Никогда не используй законы других стран.\n\n"
                "Формат ответа:\n"
                "1. Юридическая оценка\n"
                "2. Применимое законодательство\n"
                "3. Практика\n"
                "4. Судебная практика\n"
                "5. Применение закона\n"
                "6. Источники\n\n"
                "Если информация найдена через Google, используй её для уточнения ответа!"
            )},
            {"role": "user", "content": user_message}
        ]

        search_context = search_google(user_message)
        if search_context:
            messages.append({"role": "system", "content": search_context})

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages
        )
        answer = response["choices"][0]["message"]["content"]
        await context.bot.send_message(chat_id=chat_id, text=answer)

        import traceback
        except Exception as e:
        logging.error("Ошибка OpenAI:\n" + traceback.format_exc())
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
