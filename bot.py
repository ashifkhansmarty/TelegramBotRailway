import logging
import sqlite3
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)

# ---------------- CONFIG ----------------
BOT_TOKEN = "7639044509:AAH8-Uh024ffsU6E2jq9kVi2QFwJfPAARrI"
WEBHOOK_URL = "https://telegrambotrailway-2.onrender.com/webhook"  # <-- CHANGE THIS AFTER DEPLOY
API_BASE = "https://mynkapi.amit1100941.workers.dev/api"
API_KEY = "mynk01"
ADMINS = [1229178839]
MAX_CREDITS_PER_USER = 5
# ----------------------------------------

# ---------------- LOGGER ----------------
logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# ----------------------------------------

# ---------------- DATABASE ----------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(f"""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    credits INTEGER DEFAULT {MAX_CREDITS_PER_USER}
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stats(
    id INTEGER PRIMARY KEY,
    total_users INTEGER DEFAULT 0,
    total_searches INTEGER DEFAULT 0
)
""")

cursor.execute("INSERT OR IGNORE INTO stats(id,total_users,total_searches) VALUES(1,0,0)")
conn.commit()
# ------------------------------------------


# ---------------- API FUNCTION ----------------
def fetch_mobile_details(number):
    url = f"{API_BASE}?key={API_KEY}&type=mobile&term={number}"
    res = requests.get(url, timeout=5)
    return res.json()
# ----------------------------------------------


# ---------------- UTILS ----------------
def add_user(user_id, username):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users(user_id,username,credits) VALUES(?,?,?)",
            (user_id, username, MAX_CREDITS_PER_USER),
        )
        conn.commit()
        cursor.execute("UPDATE stats SET total_users = total_users + 1 WHERE id=1")
        conn.commit()


def deduct_credit(user_id):
    cursor.execute("UPDATE users SET credits = credits - 1 WHERE user_id=? AND credits > 0", (user_id,))
    conn.commit()


def get_credits(user_id):
    cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0


def increment_searches():
    cursor.execute("UPDATE stats SET total_searches = total_searches + 1 WHERE id=1")
    conn.commit()


def get_stats():
    cursor.execute("SELECT total_users, total_searches FROM stats WHERE id=1")
    return cursor.fetchone()
# ------------------------------------------


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.message.from_user.id, update.message.from_user.username or "N/A")
    keyboard = [
        [InlineKeyboardButton("📱 Lookup Mobile Number", callback_data="lookup")],
        [InlineKeyboardButton("📊 Stats Panel", callback_data="stats")],
        [InlineKeyboardButton("💳 My Credits", callback_data="mycredits")],
    ]
    await update.message.reply_text(
        "👋 Welcome! Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
# --------------------------------------


# ---------------- BUTTON HANDLER ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "lookup":
        await query.message.reply_text("📥 Send a 10-digit mobile number:")
        return

    if query.data == "stats":
        if user_id in ADMINS:
            total_users, total_searches = get_stats()
            await query.message.reply_text(
                f"📊 Stats Panel\n\nTotal Users: {total_users}\nTotal Searches: {total_searches}"
            )
        else:
            await query.message.reply_text("❌ Not authorized.")
        return

    if query.data == "mycredits":
        credits = get_credits(user_id)
        if credits > 0:
            await query.message.reply_text(f"⭐ You have {credits} credit(s) remaining.")
        else:
            await query.message.reply_text(
                "❌ You have 0 credits left.\n"
                "Please contact Admin @infoggz to refill your credits."
            )
# ------------------------------------------


# ---------------- HANDLE MOBILE NUMBER ----------------
async def handle_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    user_id = update.message.from_user.id

    add_user(user_id, update.message.from_user.username or "N/A")

    credits = get_credits(user_id)
    if credits <= 0:
        await update.message.reply_text(
            "❌ You have 0 credits left.\n"
            "Please contact Admin @infoggz to refill your credits."
        )
        return

    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text("❌ Mobile number must be exactly 10 digits.")
        return

    msg = await update.message.reply_text("🛸 Scanning number... Please wait 👽")

    try:
        data = fetch_mobile_details(number)
    except:
        await msg.edit_text("⚠ API error. Try again later.")
        return

    deduct_credit(user_id)
    increment_searches()

    if not data or "result" not in data:
        await msg.edit_text("❌ No data found for this number.")
        return

    result = data["result"]

    if isinstance(result, dict) and result.get("status") == "error":
        await msg.edit_text(f"❌ {result.get('message', 'Invalid number')}")
        return

    if isinstance(result, list) and len(result) > 0:
        context.user_data["results"] = result
        context.user_data["index"] = 0
        await send_result(msg, context)
        return

    await msg.edit_text("❌ No data found for this number.")
# ------------------------------------------


# ---------------- SEND RESULT ----------------
async def send_result(msg, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data["index"]
    results = context.user_data["results"]
    entry = results[index]

    number = entry.get("mobile", "N/A")
    name = entry.get("name", "N/A")
    father = entry.get("father_name", "N/A")
    address = entry.get("address", "N/A").replace("!!", "\n").replace("!", "\n")
    alt = entry.get("alt_mobile", "N/A").replace("91", "")
    circle = entry.get("circle", "N/A")
    idnum = entry.get("id_number", "N/A")
    email = entry.get("email", "N/A")

    text = f"""
👽 *ALIEN SCAN REPORT* 👽

📱 *Mobile:* `{number}`
🧬 *Name:* {name}
🧪 *Father:* {father}

🌍 *Address:*
{address}

📞 *Alt Mobile:* {alt}
📡 *Circle:* {circle}
🆔 *ID Number:* {idnum}
📨 *Email:* {email}
"""

    keyboard = []

    if len(results) > 1:
        buttons = []
        if index > 0:
            buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data="prev"))
        if index < len(results) - 1:
            buttons.append(InlineKeyboardButton("Next ➡️", callback_data="next"))
        keyboard.append(buttons)

    await msg.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
    )


# ---------------- NAVIGATION HANDLER ----------------
async def navigation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "next":
        context.user_data["index"] += 1
    elif data == "prev":
        context.user_data["index"] -= 1

    await send_result(query.message, context)


# ---------------- ADMIN COMMANDS ----------------
async def logs(update, context):
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("❌ Not allowed.")
        return

    await update.message.reply_document("bot.log")


async def addcredit(update, context):
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("❌ Not allowed.")
        return

    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("Usage: /addcredit <user_id> <amount>")
        return

    user_id = int(parts[1])
    amount = int(parts[2])

    cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, user_id))
        conn.commit()
        await update.message.reply_text("Added credits.")
    else:
        await update.message.reply_text("User not found.")


# ---------------- WEBHOOK SERVER ----------------
app_flask = Flask(__name__)
telegram_app = None  # filled after building application


@app_flask.post("/webhook")
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return "OK"


# ---------------- MAIN ----------------
async def setup():
    global telegram_app
    telegram_app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("logs", logs))
    telegram_app.add_handler(CommandHandler("addcredit", addcredit))

    telegram_app.add_handler(CallbackQueryHandler(button_handler, pattern="^(lookup|stats|mycredits)$"))
    telegram_app.add_handler(CallbackQueryHandler(navigation_handler, pattern="^(next|prev)$"))

    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mobile))

    await telegram_app.bot.set_webhook(WEBHOOK_URL)


import asyncio
asyncio.run(setup())

if __name__ == "__main__":
    app_flask.run(host="0.0.0.0", port=10000)

