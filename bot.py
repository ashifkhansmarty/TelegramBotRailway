import os
import sqlite3
import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_USERNAME = "ashifkhansmart"
DB_PATH = "users.db"

# ---------------- Database -----------------
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute(
    """CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        credits INTEGER DEFAULT 3
    )"""
)
conn.commit()

# ---------------- Helper Functions -----------------
def get_credits(user_id):
    cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        cursor.execute("INSERT INTO users (user_id, credits) VALUES (?, ?)", (user_id, 3))
        conn.commit()
        return 3

def deduct_credit(user_id):
    credits = get_credits(user_id)
    if credits > 0:
        cursor.execute("UPDATE users SET credits=? WHERE user_id=?", (credits-1, user_id))
        conn.commit()
        return True
    return False

# ---------------- Bot Commands -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    credits = get_credits(user_id)
    await update.message.reply_text(
        f"Welcome! You have {credits} credits.\nSend a 10-digit mobile number to search.\nCredit : ASHIF KHAN"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    credits = get_credits(user_id)
    await update.message.reply_text(f"Your credits: {credits}\nCredit : ASHIF KHAN")

# ---------------- API Request -----------------
async def fetch_mobile(number):
    url = f"https://mynkapi.amit1100941.workers.dev/api?key=mynk01&type=mobile&term={number}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# ---------------- Message Handler -----------------
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not text.isdigit() or len(text) != 10:
        await update.message.reply_text("❌ Mobile number must be exactly 10 digits.\nCredit : ASHIF KHAN")
        return

    credits = get_credits(user_id)
    if credits == 0:
        await update.message.reply_text(f"❌ You have 0 credits. Contact Admin @{ADMIN_USERNAME} for credit.\nCredit : ASHIF KHAN")
        return

    if not deduct_credit(user_id):
        await update.message.reply_text(f"❌ You have 0 credits. Contact Admin @{ADMIN_USERNAME} for credit.\nCredit : ASHIF KHAN")
        return

    msg = await update.message.reply_text("🔎 Searching...")

    try:
        data = await fetch_mobile(text)
        result = data.get("result", {})
        message = result.get("message", "No records found")
        
        if "No records found" in message:
            await msg.edit_text(f"❌ {message}\nCredit : ASHIF KHAN")
        else:
            # Inline button example for multiple results
            buttons = [[InlineKeyboardButton("View Details", callback_data=text)]]
            keyboard = InlineKeyboardMarkup(buttons)
            await msg.edit_text(f"✅ Result found for {text}\nCredit : ASHIF KHAN", reply_markup=keyboard)
    except Exception as e:
        await msg.edit_text(f"❌ Error occurred: {e}\nCredit : ASHIF KHAN")

# ---------------- Callback Query -----------------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    number = query.data
    data = await fetch_mobile(number)
    await query.edit_message_text(f"📊 Details:\n{data}\nCredit : ASHIF KHAN")

# ---------------- Main -----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot is running...")
    app.run_polling()
