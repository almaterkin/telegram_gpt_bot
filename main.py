import os
import logging
import re
import openai
import requests
import nest_asyncio
nest_asyncio.apply()
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Системный промпт
system_prompt = {
    "role": "system",
    "content": (
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
    )
}

chat_histories = {}

def clean_reply(reply):
    reply = re.sub(r'\*\*(.*?)\*\*', r'\1', reply)
    reply = re.sub(r'<strong>(.*?)</strong>', r'\1', reply)
    return reply

def search_google(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        results = data.get("items", [])
        links = "\n".join(f"- [{item['title']}]({item['link']})" for item in results[:5])
        return f"Вот результаты поиска, которые помогут тебе ответить:\n{links}"
    except Exception as e:
        logger.error(f"Google Search Error: {e}")
        return ""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id

    history = chat_histories.get(chat_id, [])
    history.append({"role": "user", "content": user_message})

    messages = [system_prompt] + history

    search_context = search_google(user_message)
    if search_context:
        messages.append({"role": "system", "content": search_context})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2
        )
        reply = response["choices"][0]["message"]["content"]
        reply = clean_reply(reply)
        history.append({"role": "assistant", "content": reply})
        chat_histories[chat_id] = history

        await context.bot.send_message(chat_id=chat_id, text=reply, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"OpenAI Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="Ошибка при обращении к ИИ.")

# ✅ Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Здравствуйте! Я — правовой консультант по законодательству Республики Казахстан. Задайте ваш вопрос."
    )

if __name__ == "__main__":
    import asyncio

    async def main():
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        # Добавляем обработчики
        app.add_handler(CommandHandler("start", start))  # обработка /start
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # обработка текстов

        webhook_url = os.getenv("WEBHOOK_URL")  # Убедитесь, что задали в Render
        port = int(os.getenv("PORT", 10000))    # Render автоматически подставит порт

        await app.bot.set_webhook(url=webhook_url)
        await app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )

    asyncio.run(main())
