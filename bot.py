import logging
import sqlite3
import time
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = "8469776408:AAHHQKrC8DPwbFCiKyvEj6RJghybWbMU7i0"
ADMIN_ID = 2069782530  # <-- your numeric Telegram ID
BOT_NAME = "@TheCoderServiceHelp_bot"
CREATOR = "Vinay Kumar"

RATE_LIMIT_SECONDS = 10
user_last_message = {}

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT,
    user_id INTEGER,
    message TEXT,
    status TEXT
)
""")

conn.commit()

# ================= UTIL =================
def generate_ticket_id():
    return "TC-" + uuid.uuid4().hex[:6].upper()

def is_spam(user_id):
    now = time.time()
    last = user_last_message.get(user_id, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    user_last_message[user_id] = now
    return False

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (user.id,))
    conn.commit()

    keyboard = [
        [InlineKeyboardButton("📢 Services", callback_data="services")],
        [InlineKeyboardButton("📞 Contact Support", callback_data="contact")],
        [InlineKeyboardButton("📚 Study Tracker Pro", callback_data="study")],
    ]

    await update.message.reply_text(
        f"👋 <b>Welcome to TheCoder Service Help</b>\n\n"
        f"🤖 Bot: <code>{BOT_NAME}</code>\n"
        f"👨‍💻 Created by <b>{CREATOR}</b>\n\n"
        f"Choose an option 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= USER MENU =================
async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "services":
        await q.edit_message_text(
            "🛠 <b>Our Services</b>\n\n"
            "1️⃣ Adsense Approval\n"
            "2️⃣ SEO Optimization\n"
            "3️⃣ Website Creation\n\n"
            "✍️ Send your requirement",
            parse_mode="HTML"
        )

    elif q.data == "contact":
        await q.edit_message_text(
            "📞 <b>Contact Support</b>\n\n"
            "Send your issue.\nAdmin will reply.",
            parse_mode="HTML"
        )

    elif q.data == "study":
        await q.edit_message_text(
            "📚 <b>Study Tracker Pro Support</b>\n\n"
            "Send your query.",
            parse_mode="HTML"
        )

# ================= USER MESSAGE =================
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_spam(user.id):
        await update.message.reply_text("⚠️ Please wait before sending again.")
        return

    ticket_id = generate_ticket_id()
    text = update.message.text or "📎 File received"

    cursor.execute(
        "INSERT INTO tickets VALUES (?, ?, ?, ?)",
        (ticket_id, user.id, text, "OPEN")
    )
    conn.commit()

    username = f"@{user.username}" if user.username else "No username"

    await context.bot.send_message(
        ADMIN_ID,
        f"🎫 <b>New Ticket</b>\n\n"
        f"🆔 <code>{ticket_id}</code>\n"
        f"👤 {user.full_name}\n"
        f"🔗 <code>{username}</code>\n\n"
        f"💬 {text}",
        parse_mode="HTML"
    )

    await update.message.reply_text(
        f"✅ Ticket Created\n\n"
        f"🎫 <code>{ticket_id}</code>",
        parse_mode="HTML"
    )

# ================= FILE HANDLER =================
async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_user_message(update, context)

# ================= ADMIN REPLY =================
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("/reply USER_ID message")
        return

    uid = int(context.args[0])
    msg = " ".join(context.args[1:])

    await context.bot.send_message(uid, f"📩 <b>Admin Reply</b>\n\n{msg}", parse_mode="HTML")
    await update.message.reply_text("✅ Reply sent")

# ================= CLOSE TICKET =================
async def close_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("/close TICKET_ID")
        return

    tid = context.args[0]

    cursor.execute("SELECT user_id, status FROM tickets WHERE ticket_id=?", (tid,))
    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("❌ Ticket not found")
        return

    user_id, status = row

    if status == "CLOSED":
        await update.message.reply_text("⚠️ Already closed")
        return

    cursor.execute("UPDATE tickets SET status='CLOSED' WHERE ticket_id=?", (tid,))
    conn.commit()

    await context.bot.send_message(
        user_id,
        f"✅ <b>Your ticket is closed</b>\n\n🎫 <code>{tid}</code>",
        parse_mode="HTML"
    )

    await update.message.reply_text(f"✅ Ticket {tid} closed")

# ================= BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("/broadcast message")
        return

    msg = " ".join(context.args)

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    sent = failed = 0
    for (uid,) in users:
        try:
            await context.bot.send_message(uid, f"📢 <b>Announcement</b>\n\n{msg}", parse_mode="HTML")
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"📊 Sent: {sent} | Failed: {failed}")

# ================= ADMIN PANEL =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast Help", callback_data="admin_broadcast_help")],
    ]

    await update.message.reply_text(
        "🧑‍💻 <b>Admin Panel</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def admin_panel_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "admin_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets")
        tickets = cursor.fetchone()[0]

        await q.edit_message_text(
            f"📊 <b>Bot Stats</b>\n\n"
            f"👥 Users: {users}\n"
            f"🎫 Tickets: {tickets}",
            parse_mode="HTML"
        )

    elif q.data == "admin_broadcast_help":
        await q.edit_message_text(
            "📢 Use:\n\n<code>/broadcast Your message</code>",
            parse_mode="HTML"
        )

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", admin_reply))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("close", close_ticket))

    # ✅ FIXED handlers with patterns
    app.add_handler(CallbackQueryHandler(user_menu, pattern="^(services|contact|study)$"))
    app.add_handler(CallbackQueryHandler(admin_panel_actions, pattern="^admin_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_files))

    print("✅ Bot running successfully")
    app.run_polling()

if __name__ == "__main__":
    main()
