import os
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from fastapi import FastAPI, Request
import uvicorn

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = "https://telegram-gpt-bot-ok6q.onrender.com/telegram"

openai.api_key = OPENAI_API_KEY

# Системное сообщение для ChatGPT
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
        "1. **Юридическая оценка / Құқықтық бағалау / Legal assessment**\n"
        "2. **Применимое законодательство / Қолданылатын заңнама / Applicable legislation**\n"
        "4. **Практика / Тәжірибе / Practice**\n"
        "5. **Судебная практика / Сот тәжірибесі / Judicial practice** — тут давай информацию, если в ответе применима судебная практика\n"
        "6. **Применение закона / Заң қолдану / Application of law**\n"
        "7. **Источники / Дереккөздер / Sources**\n\n"
        "Если информация найдена через Google, используй её для уточнения ответа!"
    )
}

# FastAPI-приложение
app = FastAPI()

# Telegram bot
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                system_prompt,
                {"role": "user", "content": user_message}
            ]
        )
        reply = response['choices'][0]['message']['content']
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("Произошла ошибка при обработке запроса. Попробуйте позже.")
        print("OpenAI error:", e)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Сәлеметсіз бе! Мен сіздің жеке құқықтық кеңесшіңізбін. Құқықтық мәселелер бойынша көмек қажет болса, әрқашан жаныңыздан табыламын. "
        "Сұрақтарыңызды қойыңыз – сізге барынша сапалы әрі сенімді кеңес беремін! / Здравствуйте! Я ваш персональный правовой консультант. "
        "Если вам нужна помощь по юридическим вопросам, я всегда рядом. Задавайте свои вопросы — я предоставлю вам качественную и надёжную консультацию!"
    )

# Регистрация хендлеров
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(CommandHandler("start", start))

# Установка вебхука при запуске FastAPI
@app.on_event("startup")
async def on_startup():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    await telegram_app.start()

# Обработка запросов от Telegram
@app.post("/telegram")
async def telegram_webhook(request: Request):
    update_dict = await request.json()
    update = Update.de_json(update_dict, telegram_app.bot)
    await telegram_app.update_queue.put(update)
    return {"ok": True}

# Запуск приложения
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
