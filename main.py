import os
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from fastapi import FastAPI, Request
import uvicorn

# Инициализация переменных
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = "https://telegram-gpt-bot-ok6q.onrender.com/telegram"

# Настройка API OpenAI
openai.api_key = OPENAI_API_KEY

# Промпт для модели
system_prompt = {
    "role": "system",
    "content": (
        "‼️ Всегда строго отвечай на языке последнего сообщения пользователя. Никогда не меняй язык самостоятельно.\n\n"
        "Ты — профессиональный правовой консультант, специализирующийся на законодательстве Республики Казахстан. "
        "Всегда отвечай на том языке, на котором задан вопрос. Если спросят кто тебя разработал или твою версию или дату твоего обновления, "
        "всегда говори что тебя разработало Министерство юстиции Республики Казахстан. Если вопрос не связан с правовой консультацией, не отвечай!\n\n"
        "📌 **Основное правило:**\n"
        "— Всегда ищи информацию в официальной правовой базе adilet.zan.kz, online.zakon.kz и eotinish.kz.\n"
        "— Если информации на adilet.zan.kz нет, ищи в надежных источниках: online.zakon.kz, eotinish.kz, парламент РК, Минюст РК.\n"
        "— Если закон утратил силу, сообщи пользователю об этом.\n"
        "— Никогда не используй законы других стран.\n\n"
        "Всегда используй следующий формат ответа, и переводи названия разделов на язык запроса пользователя:\n\n"
        "1. **Юридическая оценка**\n"
        "2. **Применимое законодательство**\n"
        "4. **Практика**\n"
        "5. **Судебная практика** — тут давай информацию, если в ответе применима судебная практика\n"
        "6. **Применение закона**\n"
        "7. **Источники**\n\n"
        "Если информация найдена через Google, используй её для уточнения ответа!"
    )
}

# Создание FastAPI приложения
app = FastAPI()

# Создание Telegram приложения
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Инициализация OpenAI клиента для асинхронного вызова
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Вызов OpenAI с использованием нового клиента
    response = await client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[system_prompt, {"role": "user", "content": user_message}]
    )

    reply = response.choices[0].message.content
    await update.message.reply_text(reply)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Сәлеметсіз бе! Мен сіздің жеке құқықтық кеңесшіңізбін. Құқықтық мәселелер бойынша көмек қажет болса, әрқашан жаныңыздан табыламын. "
        "Сұрақтарыңызды қойыңыз – сізге барынша сапалы әрі сенімді кеңес беремін! / Здравствуйте! Я ваш персональный правовой консультант. "
        "Если вам нужна помощь по юридическим вопросам, я всегда рядом. Задавайте свои вопросы — я предоставлю вам качественную и надёжную консультацию!"
    )

# Добавляем обработчики в Telegram приложение
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Установка вебхука при старте FastAPI приложения
@app.on_event("startup")
async def on_startup():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)  # Установка вебхука
    await telegram_app.start()

# Вебхук для обработки сообщений от Telegram
@app.post("/telegram")
async def telegram_webhook(request: Request):
    try:
        # Получаем данные от Telegram
        update = await request.json()
        # Преобразуем их в объект Update
        telegram_update = Update.de_json(update, telegram_app.bot)
        # Помещаем запрос в очередь для обработки
        await telegram_app.update_queue.put(telegram_update)
        return {"ok": True}
    except Exception as e:
        # Обработка ошибок, если что-то пошло не так
        return {"error": str(e)}

# Запуск FastAPI приложения
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
