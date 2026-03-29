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
def health(): return "Bot is Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHARACTER_LINK = os.getenv("CHARACTER_LINK")

# --- TOOLS ---
def get_ip_info(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        if data['status'] == 'success':
            return f"📍 **IP:** {data['query']}\n🌍 **Country:** {data['country']}\n🏙️ **City:** {data['city']}\n🏢 **ISP:** {data['isp']}"
        return "❌ Invalid IP."
    except: return "⚠️ Error."

def check_wa_status(phone):
    return f"🚫 **WhatsApp Report**\n\n📱 **Number:** {phone}\n📊 **Status:** No permanent ban detected.\n💡 *Tip: Avoid GBWhatsApp to stay safe!*"

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # MAIN MENU BUTTONS
    keyboard = [
        [InlineKeyboardButton("🔍 IP Lookup", callback_data="menu_osint")],
        [InlineKeyboardButton("🚫 WhatsApp Checker", callback_data="menu_wa")],
        [InlineKeyboardButton("💻 Coding Scripts", callback_data="menu_code")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"🛠 **Welcome to Divex Tech, {user.first_name}!**\nSelect a tool below:"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # This stops the loading spinner!
    
    print(f"DEBUG: Button pressed: {query.data}") # This shows in Render logs
    
    if query.data == "menu_osint":
        await query.edit_message_text("🔎 **OSINT Mode**\nSend me an IP address (e.g. 8.8.8.8)")
    elif query.data == "menu_wa":
        await query.edit_message_text("🚫 **WhatsApp Checker**\nSend me a phone number with + (e.g. +234...)")
    elif query.data == "menu_code":
        await query.edit_message_text("🐍 **Coding Vault**\nScripts are posted in @DivexTech")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "." in text and len(text.split(".")) == 4:
        await update.message.reply_text(get_ip_info(text), parse_mode='Markdown')
    elif text.startswith("+") or (text.isdigit() and len(text) > 9):
        await update.message.reply_text(check_wa_status(text), parse_mode='Markdown')

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    # drop_pending_updates=True is the "Magic Fix" for the Conflict error
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_interaction))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app_bot.run_polling(drop_pending_updates=True)
