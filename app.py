from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import requests
from config import TELEGRAM_TOKEN, PIXABAY_API_KEY, PEXELS_API_KEY, DEFAULT_RESULT_COUNT

# --- Pixabay Fetch ---
def fetch_pixabay_videos(query):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}&per_page={DEFAULT_RESULT_COUNT}"
    response = requests.get(url)
    data = response.json()
    return data.get("hits", [])

# --- Pexels Fetch ---
def fetch_pexels_videos(query):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={DEFAULT_RESULT_COUNT}"
    response = requests.get(url, headers=headers)
    data = response.json()
    return data.get("videos", [])

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a keyword in English or Hindi to get videos.")

# --- Video Search Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    keyboard = [
        [
            InlineKeyboardButton("Low", callback_data=f"{query}|low"),
            InlineKeyboardButton("Medium", callback_data=f"{query}|medium"),
            InlineKeyboardButton("High", callback_data=f"{query}|high"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose video quality:", reply_markup=reply_markup)

# --- Quality Button Handler ---
async def quality_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_data = update.callback_query.data
    await update.callback_query.answer()
    query, quality = query_data.split("|")
    await update.callback_query.message.reply_text(f"Searching for '{query}' videos in {quality} quality...")

    pixabay_videos = fetch_pixabay_videos(query)
    pexels_videos = fetch_pexels_videos(query)

    total_sent = 0
    for video in pixabay_videos:
        url = video['videos'][quality]['url']
        thumb = video['picture_id']
        await update.callback_query.message.reply_video(video=url)
        total_sent += 1
        if total_sent >= 10:
            break

    for video in pexels_videos:
        video_files = video['video_files']
        chosen_file = next((f for f in video_files if quality in f['quality']), None)
        if chosen_file:
            await update.callback_query.message.reply_video(video=chosen_file['link'])
            total_sent += 1
        if total_sent >= 20:
            break

# --- Main ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(quality_selected))

    app.run_polling()
