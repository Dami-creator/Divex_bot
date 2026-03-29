import os
import threading
import requests  # Add this to your requirements.txt
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# --- LIVE OSINT FUNCTION ---
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
        return "❌ Invalid IP or private address."
    except:
        return "⚠️ Error connecting to IP database."

# --- BOT LOGIC ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Simple logic: If the user sends a message that looks like an IP
    if "." in user_text and len(user_text.split(".")) == 4:
        info = get_ip_info(user_text)
        await update.message.reply_text(info, parse_mode='Markdown')
    else:
        await update.message.reply_text("🤖 I'm in Toolkit Mode. To lookup an IP, just send it to me (e.g., `8.8.8.8`).")

# --- (Keep the rest of your Start and Menu logic from the previous step) ---
