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

# --- 1. WEB SERVER (Optimized for 5-minute Cron-job) ---
app = Flask(__name__)

@app.route('/')
def health():
    # Tiny response prevents "Output too large" on your 5-minute Cron-job
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. CONFIGURATION ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHARACTER_LINK = os.getenv("CHARACTER_LINK")

# --- 3. TOOL LOGIC ---
def get_ip_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=10).json()
        if res['status'] == 'success':
            return (f"📍 **IP OSINT Result**\n\n"
                    f"🌐 **IP:** {res['query']}\n"
                    f"🌍 **Country:** {res['country']}\n"
                    f"🏙️ **City:** {res['city']}\n"
                    f"🏢 **ISP:** {res['isp']}")
        return "❌ Invalid IP address."
    except: return "⚠️ Database connection error."

def deep_phone_osint(number):
    try:
        parsed_num = phonenumbers.parse(number)
        if not phonenumbers.is_valid_number(parsed_num):
            return "❌ Invalid international format."
        
        ntype = phonenumbers.number_type(parsed_num)
        type_str = "Unknown"
        if ntype == 1: type_str = "📱 Real SIM (Mobile)"
        elif ntype == 0: type_str = "☎️ Landline (Fixed)"
        elif ntype in [3, 4, 5, 8]: type_str = "🌐 Virtual / VOIP (Fake)"
        
        location = geocoder.description_for_number(parsed_num, "en")
        isp = carrier.name_for_number(parsed_num, "en")
        search_url = f"https://www.google.com/search?q=%22{number}%22"

        return (f"📞 **Phone OSINT Report**\n\n"
                f"🔢 **Number:** {number}\n"
                f"🛡️ **Type:** {type_str}\n"
                f"📡 **Carrier:** {isp if isp else 'Private/Unknown'}\n"
                f"📍 **Location:** {location if location else 'Unknown'}\n\n"
                f"🔗 [Search Socials/Leaks]({search_url})")
    except: return "❌ Use + format (e.g. +234...)"

# --- 4. HANDLERS ---
async def is_subscribed(context, user_id):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if await is_subscribed(context, user.id):
        keyboard = [
            [InlineKeyboardButton("🔍 IP Lookup", callback_data="menu_osint")],
            [InlineKeyboardButton("📞 Phone OSINT", callback_data="menu_wa")],
            [InlineKeyboardButton("🕵️ Username Tracker", callback_data="menu_user")]
        ]
        text = f"🛠 **Divex Tech Toolkit**\nSelect your tool, {user.first_name}:"
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Join Divex Tech", url="https://t.me/divextech")],
            [InlineKeyboardButton("🔄 Verify Access", callback_data="verify")]
        ]
        text = "❌ **Access Locked**\nJoin @DivexTech to use this toolkit."
        reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message: await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else: await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "verify": await start(update, context)
    elif query.data == "menu_osint": await query.edit_message_text("🔎 **IP OSINT**\nSend an IP address.")
    elif query.data == "menu_wa": await query.edit_message_text("📞 **Phone OSINT**\nSend a number with (+).")
    elif query.data == "menu_user": await query.edit_message_text("🕵️ **Username OSINT**\nSend a social media handle.")

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
        search_link = f"https://www.google.com/search?q=site%3Ainstagram.com+{text}"
        await update.message.reply_text(f"🕵️ **Username OSINT: @{text}**\n\n🔗 [Scan Socials]({search_link})", parse_mode='Markdown')

# --- 5. STABLE STARTUP ---
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_interaction))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    
    print("Bot is listening...")
    
    # Increased timeouts to stop 'TimedOut' errors on Render
    application.run_polling(
        drop_pending_updates=True,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        pool_timeout=30
    )
