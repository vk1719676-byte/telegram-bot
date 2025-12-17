import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

USERS = set()
ticket_id = 1000


# ---------------- WEB SERVER (RENDER REQUIREMENT) ----------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")


def run_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthHandler)
    server.serve_forever()


Thread(target=run_server, daemon=True).start()


# ---------------- BOT HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    USERS.add(update.effective_user.id)

    text = (
        "🤖 *TheCoderServiceHelp Bot*\n"
        "Created by Vinay Kumar\n\n"
        "Services:\n"
        "• Adsense Approval\n"
        "• SEO Services\n"
        "• Website Creation\n"
        "• Study Tracker Pro Support\n\n"
        "Choose an option 👇"
    )

    keyboard = [
        [InlineKeyboardButton("📞 Contact Us", callback_data="contact")],
        [InlineKeyboardButton("🎫 Study Tracker Pro Support", callback_data="support")],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ticket_id
    ticket_id += 1
    user = update.callback_query.from_user
    await update.callback_query.answer()

    username = user.username or "NoUsername"

    await context.bot.send_message(
        ADMIN_ID,
        f"📩 Contact Request\n👤 @{username}\n🎫 Ticket ID: {ticket_id}"
    )

    await update.callback_query.edit_message_text(
        f"✅ Request sent!\n🎫 Ticket ID: {ticket_id}"
    )


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ticket_id
    ticket_id += 1
    user = update.callback_query.from_user
    await update.callback_query.answer()

    username = user.username or "NoUsername"

    await context.bot.send_message(
        ADMIN_ID,
        f"🆘 Study Tracker Pro Support\n👤 @{username}\n🎫 Ticket ID: {ticket_id}"
    )

    await update.callback_query.edit_message_text(
        f"🆘 Support request sent!\n🎫 Ticket ID: {ticket_id}"
    )


# ---------------- ADMIN ----------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(f"📊 Total users: {len(USERS)}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast message")
        return

    msg = " ".join(context.args)
    sent = 0

    for uid in USERS:
        try:
            await context.bot.send_message(uid, msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users")


# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(contact, pattern="contact"))
    app.add_handler(CallbackQueryHandler(support, pattern="support"))

    app.run_polling()


if __name__ == "__main__":
    main()

