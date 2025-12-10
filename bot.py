import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask
from threading import Thread

# ===================== BOT TOKEN =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# =====================================================

# -------- Telegram Handlers --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a 10-digit mobile number to fetch details.")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = update.message.text.strip()
    if not num.isdigit() or len(num) != 10:
        await update.message.reply_text("❌ Mobile number must be exactly 10 digits.")
        return

    url = f"https://mynkapi.amit1100941.workers.dev/api?key=mynk01&type=mobile&term={num}"
    try:
        response = requests.get(url, timeout=10).json()
    except:
        await update.message.reply_text("⚠️ Error fetching data.")
        return

    # Handle no result
    if isinstance(response.get("result"), dict):
        msg = response["result"].get("message")
        if msg:
            await update.message.reply_text(f"❌ {msg}\n\nCredit : ASHIF KHAN")
            return

    # Handle result list
    if isinstance(response.get("result"), list):
        messages = []
        for r in response["result"]:
            messages.append(
                f"📱 Name: {r.get('name','N/A')}\n"
                f"Mobile: {r.get('mobile','N/A')}\n"
                f"Father Name: {r.get('father_name','N/A')}\n"
                f"Address: {r.get('address','N/A')}\n"
                f"Alt Mobile: {r.get('alt_mobile','N/A')}\n"
                f"Circle: {r.get('circle','N/A')}\n"
                f"ID Number: {r.get('id_number','N/A')}\n"
                f"Email: {r.get('email','N/A')}\n"
                f"Credit : ASHIF KHAN"
            )
        await update.message.reply_text("\n\n".join(messages))

# -------- Telegram Bot Setup --------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

# -------- Flask Keep-Alive --------
flask_app = Flask("")

@flask_app.route("/")
def home():
    return "Bot is running 24/7!"

Thread(target=lambda: flask_app.run(host="0.0.0.0", port=10000)).start()

# -------- Run Telegram Bot --------
app.run_polling()
