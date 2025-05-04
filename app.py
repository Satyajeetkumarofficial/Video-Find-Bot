import os
import asyncio
import requests
from flask import Flask
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# Env variables
TELEGRAM_TOKEN = os.environ.get("7978759722:AAGXr2jJgZbW4NefFaFHnSGwLEKP8Cjizl4")
PIXABAY_API_KEY = os.environ.get("50085343-078251d5a9190de8a512b45e4")
PEXELS_API_KEY = os.environ.get("IKaFkLUIDIe0OP45i8FucqLyRHQxiEDgQ5kTEazihdh695zcpVB7k434")

app = Flask(__name__)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("नमस्ते! वीडियो खोजने के लिए /video <शब्द> लिखें।")

# /video command
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("कृपया एक खोज शब्द दें, जैसे: /video dance")
        return

    # Ask for quality
    keyboard = [
        [InlineKeyboardButton("SD", callback_data=f"q_sd|{query}"),
         InlineKeyboardButton("HD", callback_data=f"q_hd|{query}"),
         InlineKeyboardButton("Full HD", callback_data=f"q_fullhd|{query}")]
    ]
    await update.message.reply_text("कृपया क्वालिटी चुनें:", reply_markup=InlineKeyboardMarkup(keyboard))

# Quality choice handler
async def quality_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_data = update.callback_query.data
    await update.callback_query.answer()

    quality, search_query = query_data.replace("q_", "").split("|")

    # Fetch videos
    videos = fetch_pixabay_videos(search_query, quality) + fetch_pexels_videos(search_query, quality)
    if not videos:
        await update.callback_query.edit_message_text("कोई वीडियो नहीं मिला। कृपया दूसरा शब्द आजमाएं।")
        return

    for video in videos[:20]:
        await update.callback_query.message.reply_video(video["url"], thumbnail_url=video["thumb"])

    await update.callback_query.edit_message_text(f"{len(videos[:20])} वीडियो भेजे गए!")

# Fetch from Pixabay
def fetch_pixabay_videos(query, quality):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}&per_page=20"
    res = requests.get(url)
    results = []

    if res.status_code == 200:
        for hit in res.json().get("hits", []):
            videos = hit["videos"]
            if quality == "sd":
                video_url = videos["small"]["url"]
            elif quality == "hd":
                video_url = videos["medium"]["url"]
            else:
                video_url = videos["large"]["url"]
            results.append({"url": video_url, "thumb": hit["picture_id"]})
    return results

# Fetch from Pexels
def fetch_pexels_videos(query, quality):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=20"
    res = requests.get(url, headers=headers)
    results = []

    if res.status_code == 200:
        for video in res.json().get("videos", []):
            files = video["video_files"]
            file = sorted(files, key=lambda x: x["height"])  # sort by height

            if quality == "sd":
                selected = file[0]
            elif quality == "hd":
                selected = next((f for f in file if f["quality"] == "hd"), file[-1])
            else:
                selected = file[-1]

            results.append({"url": selected["link"], "thumb": video["image"]})
    return results

# Health route
@app.route("/", methods=["GET", "HEAD"])
def index():
    return "Bot is running", 200

# Run bot
async def run_bot():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("video", video))
    application.add_handler(CallbackQueryHandler(quality_choice))

    print("Telegram bot started...")
    await application.run_polling()

# Run everything
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    app.run(host="0.0.0.0", port=8080)
