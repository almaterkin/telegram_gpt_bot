import os
import openai
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    filters, ConversationHandler
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY

# Этап для выбора языка
LANGUAGE = range(1)

# Системные промты
system_prompt_ru = {
     "role": "system",
    "content": (
        "‼️ Всегда строго отвечай на русском языке.\n\n"
        "Ты — профессиональный правовой консультант, специализирующийся на законодательстве Республики Казахстан. "
        "Если вопрос не связан с правовой консультацией, не отвечай!\n\n"
        "📌 **Основное правило:**\n"
        "— Всегда ищи информацию в официальной правовой базе adilet.zan.kz, online.zakon.kz и eotinish.kz.\n"
        "— Если закон утратил силу, сообщи пользователю об этом.\n"
        "— Никогда не используй законы других стран.\n\n"
        "Формат ответа:\n"
        "1. **Юридическая оценка**\n"
        "2. **Применимое законодательство**\n"
        "3. **Практика**\n"
        "4. **Судебная практика**\n"
        "5. **Применение закона**\n"
        "6. **Источники**"
    )
}

system_prompt_kz = {
   "role": "system",
    "content": (
        "‼️ Әрқашан қазақ тілінде жауап бер.\n\n"
        "Сен – Қазақстан Республикасының заңнамасына маманданған кәсіби құқықтық кеңесшісің. "
        "Егер сұрақ құқықтық кеңеске қатысты болмаса, жауап берме!\n\n"
        "📌 **Негізгі ереже:**\n"
        "— Әрқашан ақпаратты adilet.zan.kz, online.zakon.kz және eotinish.kz ресми дереккөздерінен ізде.\n"
        "— Егер заң өз күшін жойса, бұл туралы пайдаланушыға хабарла.\n"
        "— Басқа елдердің заңдарын ешқашан қолданба.\n\n"
        "Жауап форматы:\n"
        "1. **Құқықтық бағалау**\n"
        "2. **Қолданылатын заңнама**\n"
        "3. **Тәжірибе**\n"
        "4. **Сот тәжірибесі**\n"
        "5. **Заң қолдану**\n"
        "6. **Дереккөздер**"
    )
}

# Меню для языков
def get_main_menu(lang):
    if lang == "kz":
        return ReplyKeyboardMarkup([
            ["📜 Сұрақ қою", "🌐 Тілді ауыстыру"],
            ["ℹ️ Бот туралы"]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            ["📜 Задать вопрос", "🌐 Сменить язык"],
            ["ℹ️ О боте"]
        ], resize_keyboard=True)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("Қазақ тілі"), KeyboardButton("Русский язык")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Тілді таңдаңыз / Выберите язык:", reply_markup=reply_markup)
    return LANGUAGE

# Команда /language
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("Қазақ тілі"), KeyboardButton("Русский язык")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Тілді қайта таңдаңыз / Выберите язык заново:", reply_markup=reply_markup)
    return LANGUAGE

# Обработка выбора языка
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text.lower()
    if "қазақ" in lang:
        context.user_data["lang"] = "kz"
        await update.message.reply_text("Сіз қазақ тілін таңдадыңыз. Енді құқықтық сұрақтарыңызды қойыңыз.", reply_markup=get_main_menu("kz"))
    elif "рус" in lang:
        context.user_data["lang"] = "ru"
        await update.message.reply_text("Вы выбрали русский язык. Теперь можете задать свой правовой вопрос.", reply_markup=get_main_menu("ru"))
    else:
        await update.message.reply_text("Тіл анықталмады / Язык не распознан.")
        return LANGUAGE
    return ConversationHandler.END

# Ответ на сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = context.user_data.get("lang")

    if not lang:
        await update.message.reply_text("Пожалуйста, сначала выберите язык с помощью команды /start.")
        return

    # Обработка кнопок
    if user_message in ["🌐 Сменить язык", "🌐 Тілді ауыстыру"]:
        return await language(update, context)

    if user_message in ["ℹ️ О боте", "ℹ️ Бот туралы"]:
        msg = (
            "🤖 Я создан Министерством юстиции Республики Казахстан для помощи в правовых вопросах."
            if lang == "ru"
            else "🤖 Мен Қазақстан Республикасының Әділет министрлігімен құқықтық көмек көрсету үшін жасалғанмын."
        )
        await update.message.reply_text(msg, reply_markup=get_main_menu(lang))
        return

    if user_message in ["📜 Задать вопрос", "📜 Сұрақ қою"]:
        await update.message.reply_text(
            "Пожалуйста, напишите ваш правовой вопрос 👇" if lang == "ru"
            else "Өтінемін, құқықтық сұрағыңызды жазыңыз 👇"
        )
        return

    # Генерация ответа
    prompt = system_prompt_kz if lang == "kz" else system_prompt_ru

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[prompt, {"role": "user", "content": user_message}]
        )
        reply = response['choices'][0]['message']['content']
        await update.message.reply_text(reply, reply_markup=get_main_menu(lang))
    except Exception as e:
        await update.message.reply_text("⚠️ Қате орын алды / Произошла ошибка.")
        print("OpenAI error:", e)

# Запуск бота
async def main():
    if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
        raise ValueError("One or more environment variables are missing.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("language", language)],
        states={LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)]},
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.bot.set_webhook(WEBHOOK_URL)
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

