import os
import threading
import requests
from flask import Flask
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import TELEGRAM_TOKEN, PIXABAY_API_KEY, PEXELS_API_KEY

app = Flask(__name__)

# Home route for Koyeb health check
@app.route("/")
def home():
    return "Bot is running!"

# Function to fetch video from Pixabay
def fetch_pixabay_video(query):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}"
    res = requests.get(url).json()
    hits = res.get("hits")
    if hits:
        video_url = hits[0]["videos"]["medium"]["url"]
        return video_url
    return None

# Function to fetch video from Pexels
def fetch_pexels_video(query):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
    res = requests.get(url, headers=headers).json()
    videos = res.get("videos")
    if videos:
        return videos[0]["video_files"][0]["link"]
    return None

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! Mujhe /video <search term> bhejein aur main video dhoondh ke launga!")

# /video command
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kripya video ka keyword dein. Udaharan: /video nature")
        return

    query = " ".join(context.args)
    video_url = fetch_pixabay_video(query) or fetch_pexels_video(query)

    if video_url:
        await update.message.reply_video(video_url)
    else:
        await update.message.reply_text("Koi video nahi mila. Dusra keyword try karein.")

# Set Telegram Bot Commands
async def set_commands(application):
    commands = [
        BotCommand("start", "Bot ko shuru kare aur instructions de"),
        BotCommand("video", "Video search kare Pexels aur Pixabay par")
    ]
    await application.bot.set_my_commands(commands)

# Telegram bot run function
async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("video", video))

    await set_commands(application)
    await application.run_polling()

def run_bot():
    import asyncio
    asyncio.run(main())

# Run Flask + Bot in separate thread
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
