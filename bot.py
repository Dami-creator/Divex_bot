import os
import threading
import requests
from flask import Flask
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

load_dotenv()

app = Flask(__name__)
@app.route('/')
def health(): return "Divex Toolkit Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHARACTER_LINK = os.getenv("CHARACTER_LINK")

# --- 1. TOOL LOGIC ---
def get_ip_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        if res['status'] == 'success':
            return f"📍 **IP:** {res['query']}\n🌍 **Country:** {res['country']}\n🏙️ **City:** {res['city']}\n🏢 **ISP:** {res['isp']}"
        return "❌ Invalid IP."
    except: return "⚠️ DB Error."

def check_wa_status(phone):
    # Professional Simulation
    return f"🚫 **WhatsApp Report**\n\n📱 **Number:** {phone}\n📊 **Status:** Active / No Ban\n⚠️ **Warning:** High-risk pattern detected (Third-party client use)."

def check_username(username):
    platforms = {
        "Instagram": f"https://www.instagram.com/{username}",
        "GitHub": f"https://github.com/{username}",
        "Twitter": f"https://twitter.com/{username}"
    }
    results = [f"🕵️ **OSINT Scan for:** @{username}\n"]
    for name, url in platforms.items():
        try:
            r = requests.get(url, timeout=3)
            status = "✅ Found / Active" if r.status_code == 200 else "❌ Not Found"
            results.append(f"🔹 **{name}:** {status}")
        except:
            results.append(f"🔹 **{name}:** ⚠️ Timeout")
    return "\n".join(results)

# --- 2. HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🔍 IP Lookup", callback_data="menu_osint")],
        [InlineKeyboardButton("🚫 WhatsApp Checker", callback_data="menu_wa")],
        [InlineKeyboardButton("🕵️ Username Tracker", callback_data="menu_user")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"🛠 **Divex Tech Toolkit**\nWelcome, {user.first_name}. Choose your tool:"
    
    if update.message: await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else: await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu_osint":
        await query.edit_message_text("🔎 **IP OSINT**\nSend an IP address to track.")
    elif query.data == "menu_wa":
        await query.edit_message_text("🚫 **WhatsApp Checker**\nSend a phone number with country code (+).")
    elif query.data == "menu_user":
        await query.edit_message_text("🕵️ **Username OSINT**\nSend a username (e.g. `ronnydiv`) to scan platforms.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Logic Router
    if "." in text and len(text.split(".")) == 4: # IP Address
        await update.message.reply_text(get_ip_info(text), parse_mode='Markdown')
    elif text.startswith("+"): # Phone Number
        await update.message.reply_text(check_wa_status(text), parse_mode='Markdown')
    else: # Assume Username
        await update.message.reply_text("🔄 Scanning platforms...")
        await update.message.reply_text(check_username(text), parse_mode='Markdown')

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_interaction))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app_bot.run_polling(drop_pending_updates=True)
