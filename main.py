import os
import openai
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import logging

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY

PROMPTS = {
    "ru": {
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
            "Всегда используй следующий формат ответа:\n\n"
            "1. **Юридическая оценка**\n"
            "2. **Применимое законодательство**\n"
            "3. **Практика**\n"
            "4. **Судебная практика**\n"
            "5. **Применение закона**\n"
            "6. **Источники**"
        )
    },
    "kz": {
        "role": "system",
        "content": (
            "‼️ Әрқашан пайдаланушының соңғы хабарламасының тілінде қатаң жауап бер. Ешқашан тілді өздігінен өзгертпе.\n\n"
            "Сен — Қазақстан Республикасы заңнамасына маманданған кәсіби құқықтық кеңесшісің. "
            "Сұрақ қай тілде қойылса, сол тілде жауап бер. Егер кім сені кім әзірлегенін, нұсқаңды немесе соңғы жаңартылған күніңді сұраса — "
            "әрқашан сені Қазақстан Республикасы Әділет министрлігі әзірлеген деп айт. Құқықтық кеңеске қатысы жоқ сұрақтарға жауап берме!\n\n"
            "📌 **Негізгі ереже:**\n"
            "— Әрқашан ақпаратты adilet.zan.kz, online.zakon.kz және eotinish.kz ресми құқықтық базасынан ізде.\n"
            "— Егер ақпарат adilet.zan.kz сайтында жоқ болса, сенімді дереккөздерден ізде: online.zakon.kz, eotinish.kz, ҚР Парламенті, ҚР Әділет министрлігі.\n"
            "— Егер заң өз күшін жойса — пайдаланушыға бұл туралы хабарла.\n"
            "— Басқа елдердің заңдарын ешқашан қолданба.\n\n"
            "Келесі жауап құрылымын пайдалан:\n\n"
            "1. **Құқықтық бағалау**\n"
            "2. **Қолданылатын заңнама**\n"
            "3. **Тәжірибе**\n"
            "4. **Сот тәжірибесі**\n"
            "5. **Заң қолдану**\n"
            "6. **Дереккөздер**"
        )
    }
}

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start вызван. Update: {update.to_dict()}")
    message = update.message or update.effective_message
    if not message:
        logger.warning("⚠️ update.message is None. Невозможно отправить меню.")
        return

    keyboard = [
        [InlineKeyboardButton("Қазақ тілі", callback_data="kz")],
        [InlineKeyboardButton("Русский язык", callback_data="ru")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Тілді таңдаңыз / Выберите язык:", reply_markup=reply_markup)

# Обработка выбора языка
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

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = context.user_data.get("lang")

    if not lang:
        await update.message.reply_text("⛔ Сначала выберите язык с помощью команды /start")
        return

    logger.info(f"Получено сообщение от пользователя {update.message.from_user.id}: {user_message}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[PROMPTS[lang], {"role": "user", "content": user_message}]
        )
        reply = response["choices"][0]["message"]["content"]
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"OpenAI ошибка: {e}")
        await update.message.reply_text("⚠️ Қате орын алды / Произошла ошибка. Попробуйте позже.")

# Запуск приложения
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if WEBHOOK_URL:
        await app.bot.set_webhook(WEBHOOK_URL)
        await app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 5000)),
            webhook_url=WEBHOOK_URL
        )
    else:
        logger.error("WEBHOOK_URL не установлен.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
