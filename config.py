import os

# Environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
DEFAULT_RESULT_COUNT = int(os.getenv('DEFAULT_RESULT_COUNT', 10))  # Default value if not set
