import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Сәлеметсіз бе! Мен сіздің жеке құқықтық кеңесшіңізбін. Құқықтық мәселелер бойынша көмек қажет болса, әрқашан жаныңыздан табыламын. Сұрақтарыңызды қойыңыз – сізге барынша сапалы әрі сенімді кеңес беремін! / Здравствуйте! Я ваш персональный правовой консультант. Если вам нужна помощь по юридическим вопросам, я всегда рядом. Задавайте свои вопросы — я предоставлю вам качественную и надёжную консультацию!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_message}]
    )

    reply = response['choices'][0]['message']['content']
    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
