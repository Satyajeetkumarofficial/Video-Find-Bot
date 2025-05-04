import os
import requests
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from config import TELEGRAM_TOKEN, PIXABAY_API_KEY, PEXELS_API_KEY, DEFAULT_RESULT_COUNT

app = Flask(__name__)

# Function to search videos from Pixabay
def search_videos_pixabay(query, num_results=5):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}&per_page={num_results}"
    response = requests.get(url).json()
    video_results = []
    for video in response.get("hits", []):
        video_url = video["videos"]["large"]["url"]
        thumbnail_url = video["preview"]["webformatURL"]
        video_results.append({"video_url": video_url, "thumbnail": thumbnail_url})
    return video_results

# Function to search videos from Pexels
def search_videos_pexels(query, num_results=5):
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={num_results}"
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    response = requests.get(url, headers=headers).json()
    video_results = []
    for video in response.get("videos", []):
        video_url = video["video_files"][0]["link"]
        thumbnail_url = video["image"]
        video_results.append({"video_url": video_url, "thumbnail": thumbnail_url})
    return video_results

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! Send me a keyword, and I’ll find videos for you. Example: 'dogs' or 'nature'.")

# Function to handle user messages (search query)
async def search_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query or query.lower() == "/start":
        return

    # Ask user for the number of results they want
    await update.message.reply_text("How many results would you like to receive? (Default: 5)")
    await update.message.reply_text(f"Searching videos for '{query}'...")

    # Search for videos using both APIs (Pixabay and Pexels)
    num_results = DEFAULT_RESULT_COUNT  # Default result count
    videos_pixabay = search_videos_pixabay(query, num_results)
    videos_pexels = search_videos_pexels(query, num_results)

    # Combine both sources' results
    all_videos = videos_pixabay + videos_pexels

    # Send video URLs with thumbnails to user
    for idx, video in enumerate(all_videos):
        message = f"Video {idx+1}:\n{video['video_url']}\nThumbnail: {video['thumbnail']}"
        await update.message.reply_text(message)

# Function to run the Telegram bot
def run_bot():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_videos))
    application.run_polling()

# Run the bot in the background using threading
threading.Thread(target=run_bot).start()

# Flask route for health check (important for Koyeb)
@app.route("/")
def home():
    return "Telegram Video Bot is live!"

# Main entry for Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
