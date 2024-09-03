import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Assign environment variables to Python variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
HN_API_URL = 'https://hacker-news.firebaseio.com/v0/topstories.json'
HN_ITEM_URL = 'https://hacker-news.firebaseio.com/v0/item/{}.json'
READABILITY_API_URL = 'https://readability-bot.vercel.app/api/readability'
POSTED_STORIES_FILE = 'posted_stories.txt'
