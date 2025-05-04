import os
import logging
import requests
from config import TELEGRAM_TOKEN, PIXABAY_API_KEY, PEXELS_API_KEY, DEFAULT_RESULT_COUNT
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.environ["TELEGRAM_TOKEN"]
PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]
PEXELS_KEY = os.environ["PEXELS_API_KEY"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)

# Bot app init
application = Application.builder().token(TOKEN).build()


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("High", callback_data="high"),
            InlineKeyboardButton("Medium", callback_data="medium"),
            InlineKeyboardButton("Low", callback_data="low"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Aapko kis quality mein media chahiye?", reply_markup=reply_markup)


# Quality selector
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["quality"] = query.data
    await query.edit_message_text(text=f"Quality select ki gayi: {query.data}\nAb aap search term bhejein.")


# Search handler
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    quality = context.user_data.get("quality", "medium")
    await update.message.reply_text(f"'{query}' ke liye media dhunda ja raha hai...")

    results = get_pixabay(query, quality) + get_pexels(query, quality)
    results = results[:50]

    if not results:
        await update.message.reply_text("Kuch nahi mila.")
        return

    for video in results:
        try:
            await update.message.reply_video(video=video['video_url'], caption=video['thumbnail_url'])
        except Exception as e:
            logger.warning(f"Video send failed: {e}")


# Pixabay - Videos Fetch
def get_pixabay(query, quality):
    q_map = {"high": "largeImageURL", "medium": "webformatURL", "low": "previewURL"}
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={requests.utils.quote(query)}&video_type=movie&per_page=25"
    res = requests.get(url).json()
    return [{
        'video_url': video['videos']['large']['url'],
        'thumbnail_url': video['videos']['preview']['url']
    } for video in res.get("hits", [])]


# Pexels - Videos Fetch
def get_pexels(query, quality):
    s_map = {"high": "original", "medium": "medium", "low": "small"}
    url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=25"
    headers = {"Authorization": PEXELS_KEY}
    res = requests.get(url, headers=headers).json()
    return [{
        'video_url': video['video_files'][0]['link'],
        'thumbnail_url': video['video_files'][0]['thumbnail']
    } for video in res.get("videos", [])]


# Telegram webhook endpoint
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"


# Set webhook when app starts
def init_bot():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    application.bot.set_webhook(WEBHOOK_URL)


if __name__ == "__main__":
    app.run(port=8080)
