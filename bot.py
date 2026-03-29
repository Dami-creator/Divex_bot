import os
import threading
import requests
from flask import Flask
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Load variables from .env
load_dotenv()

# --- 1. WEB SERVER (For Render Uptime) ---
app = Flask(__name__)
@app.route('/')
def health(): return "Toolkit Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. CONFIG & OSINT LOGIC ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHARACTER_LINK = os.getenv("CHARACTER_LINK")

def get_ip_info(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        if data['status'] == 'success':
            return (f"📍 **IP Lookup Result**\n\n"
                    f"🌐 **IP:** {data['query']}\n"
                    f"🌍 **Country:** {data['country']}\n"
                    f"🏙️ **City:** {data['city']}\n"
                    f"🏢 **ISP:** {data['isp']}\n"
                    f"📡 **Org:** {data['org']}")
        return "❌ Invalid IP address."
    except:
        return "⚠️ Database error."

# --- 3. MENUS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            keyboard = [
                [InlineKeyboardButton("🔍 IP Lookup (OSINT)", callback_data="menu_osint")],
                [InlineKeyboardButton("💻 Coding Scripts", callback_data="menu_code")],
                [InlineKeyboardButton("🎮 Gaming Configs", callback_data="menu_game")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("🛠 **Damilola's Tech Toolkit**\nChoose a tool:", reply_markup=reply_markup)
        else:
            await force_follow(update)
    except:
        await force_follow(update)

async def force_follow(update: Update):
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")],
        [InlineKeyboardButton("👤 Follow Character", url=CHARACTER_LINK)],
        [InlineKeyboardButton("🔄 Verify Access", callback_data="verify")]
    ]
    await update.message.reply_text("❌ **Access Locked**\nJoin the channel to unlock!", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 4. HANDLERS ---
async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "verify": await start(query, context)
    elif query.data == "menu_osint": await query.edit_message_text("🔎 Send me an IP to track it!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "." in text and len(text.split(".")) == 4:
        await update.message.reply_text(get_ip_info(text), parse_mode='Markdown')

# --- 5. RUNNER ---
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_interaction))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app_bot.run_polling()
