from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import threading
import os
import requests

app = Flask(__name__)

# Environment Variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! /video <keyword> likhkar videos dhoondho.")

# /video command
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kripya keyword dein. Udaharan: /video nature")
        return

    query = " ".join(context.args)
    results = []

    # Pexels video search
    headers = {"Authorization": PEXELS_API_KEY}
    pexels = requests.get(f"https://api.pexels.com/videos/search?query={query}&per_page=1", headers=headers)
    if pexels.ok and pexels.json()["videos"]:
        results.append(pexels.json()["videos"][0]["video_files"][0]["link"])

    # Pixabay video search
    pixabay = requests.get(f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}")
    if pixabay.ok and pixabay.json()["hits"]:
        results.append(pixabay.json()["hits"][0]["videos"]["medium"]["url"])

    if results:
        for link in results:
            await update.message.reply_text(link)
    else:
        await update.message.reply_text("Koi video nahi mila.")

# Telegram Bot Thread
def run_bot():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("video", video))
    application.run_polling()

# Start Telegram bot in background
threading.Thread(target=run_bot).start()

# Flask route
@app.route("/")
def home():
    return "Telegram bot chal raha hai!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
