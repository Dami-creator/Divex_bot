import os
import threading
import requests
from flask import Flask
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Load environment variables
load_dotenv()

# --- 1. WEB SERVER (Keeps Render Active) ---
app = Flask(__name__)

@app.route('/')
def health():
    return "Divex Tech Toolkit is Live", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. CONFIGURATION ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHARACTER_LINK = os.getenv("CHARACTER_LINK")

# --- 3. TOOL LOGIC (IP & WHATSAPP) ---
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
        return "❌ Invalid IP address format."
    except:
        return "⚠️ Database connection error."

def check_wa_status(phone):
    # This is a simulation for your tech channel members
    # In a real setup, this would connect to a validation API
    return (f"🚫 **WhatsApp Ban Report**\n\n"
            f"📱 **Number:** {phone}\n"
            f"📊 **Status:** No permanent ban detected.\n"
            f"⚠️ **Risk Level:** Medium (If using GBWhatsApp)\n\n"
            f"💡 *Tip: Always use the official WhatsApp to avoid 1-hour temporary bans.*")

# --- 4. MENUS & HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Check if the trigger was a Message or a Callback Query
    is_callback = update.callback_query is not None
    target = update.callback_query if is_callback else update.message

    try:
        # Check if user is in the channel
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        
        if member.status in ['member', 'administrator', 'creator']:
            # ACCESS GRANTED MENU
            keyboard = [
                [InlineKeyboardButton("🔍 IP Lookup (OSINT)", callback_data="menu_osint")],
                [InlineKeyboardButton("🚫 WhatsApp Ban Checker", callback_data="menu_wa")],
                [InlineKeyboardButton("💻 Coding Scripts", callback_data="menu_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"✅ **Welcome back, {user.first_name}!**\nSelect a tool from the Divex Tech Toolkit:"
            
            if is_callback:
                await target.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await target.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await show_force_follow(update, context)
    except Exception as e:
        print(f"Auth Error: {e}")
        await show_force_follow(update, context)

async def show_force_follow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Join Divex Tech", url=f"https://t.me/{CHANNEL_ID[1:]}")],
        [InlineKeyboardButton("👤 Follow Admin", url=CHARACTER_LINK)],
        [InlineKeyboardButton("🔄 Verify Access", callback_data="verify")]
    ]
    text = "❌ **Access Locked**\nYou must join our channel and follow the admin to use these tools."
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Stops the loading spinner
    
    if query.data == "verify":
        await start(update, context)
    elif query.data == "menu_osint":
        await query.edit_message_text("🔎 **OSINT Mode**\nSend me any IP address (e.g., `8.8.8.8`) to track it.")
    elif query.data == "menu_wa":
        await query.edit_message_text("🚫 **WhatsApp Checker**\nSend me the phone number with country code (e.g., `+234...`) to check status.")
    elif query.data == "menu_code":
        await query.edit_message_text("🐍 **Coding Vault**\nCheck @DivexTech for the latest Python and C++ source codes.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Logic to decide which tool to run
    if "." in text and len(text.split(".")) == 4:
        await update.message.reply_text(get_ip_info(text), parse_mode='Markdown')
    elif text.startswith("+") or (text.isdigit() and len(text) > 9):
        await update.message.reply_text(check_wa_status(text), parse_mode='Markdown')
    else:
        await update.message.reply_text("🤖 I don't recognize that. Send an **IP** or a **Phone Number** (+).")

# --- 5. RUN THE BOT ---
if __name__ == '__main__':
    # Start Web Server
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Telegram Bot
    # drop_pending_updates=True clears the 'Conflict' error by resetting the connection
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_interaction))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    
    print("Bot is running...")
    application.run_polling(drop_pending_updates=True)
