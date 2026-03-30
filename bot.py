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

# --- 1. WEB SERVER (FIXED FOR RENDER) ---
app = Flask(__name__)

@app.route('/')
def health():
    return "Divex OSINT is Online", 200

def run_flask():
    # Render provides the PORT variable automatically
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHARACTER_LINK = os.getenv("CHARACTER_LINK")

# --- 3. OSINT TOOLS ---
def get_ip_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        if res['status'] == 'success':
            return f"📍 **IP:** {res['query']}\n🌍 **Country:** {res['country']}\n🏙️ **City:** {res['city']}\n🏢 **ISP:** {res['isp']}"
        return "❌ Invalid IP."
    except: return "⚠️ Database Error."

def deep_phone_osint(number):
    try:
        parsed_num = phonenumbers.parse(number)
        if not phonenumbers.is_valid_number(parsed_num):
            return "❌ Invalid international format."
        
        # Identify Number Type
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

def check_username(username):
    platforms = {"Instagram": f"https://www.instagram.com/{username}", "GitHub": f"https://github.com/{username}"}
    results = [f"🕵️ **Username Scan:** @{username}\n"]
    for name, url in platforms.items():
        try:
            r = requests.get(url, timeout=3)
            results.append(f"🔹 **{name}:** {'✅ Found' if r.status_code == 200 else '❌ Not Found'}")
        except: results.append(f"🔹 **{name}:** ⚠️ Timeout")
    return "\n".join(results)

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
                    [InlineKeyboardButton("📞 Phone OSINT", callback_data="menu_wa")],
                    [InlineKeyboardButton("🕵️ Username Tracker", callback_data="menu_user")]]
        text = f"🛠 **Divex Tech Toolkit**\nSelect your tool, {user.first_name}:"
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/divextech")],
                    [InlineKeyboardButton("🔄 Verify Access", callback_data="verify")]]
        text = "❌ **Access Locked**\nJoin @DivexTech to use this toolkit."
        reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message: await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else: await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "verify": await start(update, context)
    elif query.data == "menu_osint": await query.edit_message_text("🔎 **IP OSINT**\nSend an IP address.")
    elif query.data == "menu_wa": await query.edit_message_text("📞 **Phone OSINT**\nSend a number with country code (+).")
    elif query.data == "menu_user": await query.edit_message_text("🕵️ **Username OSINT**\nSend a username.")

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
        await update.message.reply_text(check_username(text), parse_mode='Markdown')

# --- 5. RUN ---
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_interaction))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    # Reset connection and start
    app_bot.run_polling(drop_pending_updates=True)
