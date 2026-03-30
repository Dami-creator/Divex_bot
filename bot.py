import os
import threading
import requests
import phonenumbers
from phonenumbers import carrier, geocoder
from flask import Flask
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

load_dotenv()

# --- 1. WEB SERVER ---
app = Flask(__name__)

@app.route('/')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# --- 3. TOOLS ---
def get_ip_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=10).json()
        if res['status'] == 'success':
            return (f"📍 **IP OSINT**\n\n"
                    f"🌐 **IP:** {res['query']}\n"
                    f"🌍 **Country:** {res['country']}\n"
                    f"🏙️ **City:** {res['city']}\n"
                    f"🏢 **ISP:** {res['isp']}")
        return "❌ Invalid IP."
    except: return "⚠️ Connection error."

def deep_phone_osint(number):
    try:
        parsed_num = phonenumbers.parse(number)
        if not phonenumbers.is_valid_number(parsed_num):
            return "❌ Invalid format."
        ntype = phonenumbers.number_type(parsed_num)
        type_str = "📱 Real SIM" if ntype == 1 else "🌐 Virtual/VOIP"
        location = geocoder.description_for_number(parsed_num, "en")
        isp = carrier.name_for_number(parsed_num, "en")
        search_url = f"https://www.google.com/search?q=%22{number}%22"
        return (f"📞 **Phone OSINT**\n\n🔢 **Number:** {number}\n🛡️ **Type:** {type_str}\n"
                f"📡 **Carrier:** {isp if isp else 'Private'}\n📍 **Location:** {location}\n\n"
                f"🔗 [Search Socials]({search_url})")
    except: return "❌ Use + format."

# --- 4. HANDLERS ---
async def is_subscribed(context, user_id):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if await is_subscribed(context, user.id):
        keyboard = [[InlineKeyboardButton("🔍 IP Lookup", callback_data="menu_osint")],
                    [InlineKeyboardButton("📞 Phone OSINT", callback_data="menu_wa")]]
        text = f"🛠 **Divex Tech Toolkit**\nSelect a tool:"
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/divextech")],
                    [InlineKeyboardButton("🔄 Verify Access", callback_data="verify")]]
        text = "❌ **Access Locked**\nJoin @DivexTech to unlock."
        reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message: await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else: await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "verify": await start(update, context)
    elif query.data == "menu_osint": await query.edit_message_text("🔎 Send an IP.")
    elif query.data == "menu_wa": await query.edit_message_text("📞 Send a number with (+).")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(context, update.effective_user.id):
        await start(update, context)
        return
    text = update.message.text.strip()
    if "." in text and len(text.split(".")) == 4:
        await update.message.reply_text(get_ip_info(text), parse_mode='Markdown')
    elif text.startswith("+"):
        await update.message.reply_text(deep_phone_osint(text), parse_mode='Markdown')
    else:
        await update.message.reply_text(f"🕵️ **Search: @{text}**\n\n🔗 [Scan Socials](https://www.google.com/search?q=site%3Ainstagram.com+{text})", parse_mode='Markdown')

# --- 5. STARTUP ---
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_interaction))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    
    print("Bot is listening...")
    # Clean run with no conflicting arguments
    application.run_polling(drop_pending_updates=True)
