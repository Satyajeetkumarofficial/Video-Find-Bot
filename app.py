import os
from flask import Flask
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import requests
import asyncio

# Config from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
DEFAULT_RESULT_COUNT = int(os.getenv("DEFAULT_RESULT_COUNT", 10))

# Flask for Koyeb health check
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return 'Telegram Bot is running!'

# Bot Handlers
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("आप क्या वीडियो सर्च करना चाहते हैं? हिंदी या English में बताएं!")

async def help_command(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("बस कोई भी शब्द भेजिए, मैं आपको Pixabay और Pexels से वीडियो दूंगा!")

async def handle_message(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.reply_text("आपको कितने वीडियो चाहिए? (उदाहरण: 10, 20, 50)")

    # Wait for next message (quality or count), skipping that for simplicity
    count = DEFAULT_RESULT_COUNT

    pixabay = fetch_pixabay_videos(query, count)
    pexels = fetch_pexels_videos(query, count)

    for item in pixabay + pexels:
        await update.message.reply_video(video=item['video'], caption=item['title'], thumbnail=item['thumbnail'])

def fetch_pixabay_videos(query, count):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}&per_page={count}"
    res = requests.get(url).json()
    results = []
    for hit in res.get("hits", []):
        video_url = hit['videos']['medium']['url']
        results.append({
            "title": hit.get("tags", "Pixabay Video"),
            "video": video_url,
            "thumbnail": hit.get("picture_id") and f"https://i.vimeocdn.com/video/{hit['picture_id']}_295x166.jpg"
        })
    return results

def fetch_pexels_videos(query, count):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={count}"
    res = requests.get(url, headers=headers).json()
    results = []
    for video in res.get("videos", []):
        video_url = video['video_files'][0]['link']
        thumbnail = video['image']
        results.append({
            "title": video.get("url", "Pexels Video"),
            "video": video_url,
            "thumbnail": thumbnail
        })
    return results

# Main Telegram bot logic
async def telegram_main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await application.run_polling()

# Launch both Flask and Telegram
if __name__ == "__main__":
    # Start Telegram Bot in asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(telegram_main())

    # Start Flask for Koyeb
    flask_app.run(host="0.0.0.0", port=8080)
