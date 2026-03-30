import os
import threading
import requests
import phonenumbers
from phonenumbers import carrier, geocoder, number_type
from flask import Flask
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

load_dotenv()

# --- WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def health(): return "Divex OSINT Live", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHARACTER_LINK = os.getenv("CHARACTER_LINK")

# --- OSINT TOOLS ---
def deep_phone_osint(number):
    try:
        parsed_num = phonenumbers.parse(number)
        if not phonenumbers.is_valid_number(parsed_num):
            return "❌ This is not a valid international number."
        
        # Identify Number Type (SIM vs Virtual)
        ntype = phonenumbers.number_type(parsed_num)
        type_str = "Unknown"
        if ntype == 1: type_str = "📱 Real SIM (Mobile)"
        elif ntype == 0: type_str = "☎️ Landline (Fixed Line)"
        elif ntype in [3, 4, 5, 8]: type_str = "🌐 Virtual / VOIP (Fake Number)"
        elif ntype == 2: type_str = "📱 Mobile/Fixed (Shared)"
        
        # Get Details
        location = geocoder.description_for_number(parsed_num, "en")
        isp = carrier.name_for_number(parsed_num, "en")
        
        # Generate Social Search Link (The "Search Socials" button logic)
        search_url = f"https://www.google.com/search?q=%22{number}%22"

        return (f"📞 **Phone OSINT Report**\n\n"
                f"🔢 **Number:** {number}\n"
                f"🛡️ **Type:** {type_str}\n"
                f"📡 **Carrier:** {isp if isp else 'Private/Unknown'}\n"
                f"📍 **Location:** {location if location else 'Unknown'}\n\n"
                f"🔗 **Manual Search:** [Click to search socials]({search_url})")
    except Exception as e:
        return "❌ Error: Use international format (e.g., +23480...)"

# --- (Keep your existing IP and Username functions here) ---

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
            [InlineKeyboardButton("📞 Phone OSINT (SIM/Virtual)", callback_data="menu_wa")],
            [InlineKeyboardButton("🕵️ Username Tracker", callback_data="menu_user")]
        ]
        text = f"🛠 **Divex Tech Toolkit**\nTarget locked. Select your tool:"
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        # Use the ID or @divextech link
        keyboard = [[InlineKeyboardButton("📢 Join Divex Tech", url="https://t.me/divextech")],
                    [InlineKeyboardButton("🔄 Verify Access", callback_data="verify")]]
        text = "❌ **Access Locked**\nYou must be in @DivexTech to use this toolkit."
        reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message: await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else: await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# --- (Keep your existing interaction and text handlers) ---
# --- IMPORTANT: Ensure handle_text calls deep_phone_osint(text) when it sees a '+' ---

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_interaction))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app_bot.run_polling(drop_pending_updates=True)
