import requests
import urllib.parse
import logging
import time
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, HN_API_URL, HN_ITEM_URL, READABILITY_API_URL, POSTED_STORIES_FILE
from typing import Tuple, Optional, Set, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_top_stories(session: requests.Session) -> List[int]:
    """Fetch the top stories from Hacker News API."""
    try:
        response = session.get(HN_API_URL)
        response.raise_for_status()
        return response.json()[:30]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch top stories: {e}")
        return []

def load_posted_stories() -> Set[str]:
    """Load the IDs of stories that have already been posted."""
    try:
        with open(POSTED_STORIES_FILE, 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

def save_posted_story(story_id: int) -> None:
    """Save the ID of a posted story to prevent reposting."""
    with open(POSTED_STORIES_FILE, 'a') as file:
        file.write(f'{story_id}\n')

def generate_instant_view_url(session: requests.Session, hn_item_id: int) -> Tuple[Optional[str], Optional[str]]:
    """Generate the Instant View URL for a Hacker News story."""
    try:
        hn_item_response = session.get(HN_ITEM_URL.format(hn_item_id))
        hn_item_response.raise_for_status()
        hn_item_data = hn_item_response.json()
        article_url = hn_item_data.get('url')
        if article_url:
            readable_url = f'{READABILITY_API_URL}?url={urllib.parse.quote(article_url, safe="")}'
            iv_url = f'https://t.me/iv?url={urllib.parse.quote(readable_url, safe="")}&rhash=71b64d09b0a20d'
            return iv_url, article_url
        else:
            logger.warning(f"No URL found for story ID: {hn_item_id}")
            return None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch item {hn_item_id}: {e}")
        return None, None

def send_message_to_telegram(session: requests.Session, message: str) -> None:
    """Send a message to the Telegram channel."""
    data = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = session.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage', json=data)
        response.raise_for_status()
        logger.info(f"Message sent to Telegram: {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to Telegram: {e}")

def main():
    session = requests.Session()
    top_stories = fetch_top_stories(session)
    posted_stories = load_posted_stories()

    for story_id in top_stories:
        if str(story_id) not in posted_stories:
            iv_url, article_url = generate_instant_view_url(session, story_id)
            if iv_url:
                message = (
                    f'<a href="{iv_url}">Read full article (Instant View)</a>\n'
                    f'Original article: <a href="{article_url}">{article_url}</a>\n'
                    f'Comments: <a href="https://news.ycombinator.com/item?id={story_id}">Hacker News Comments</a>'
                )
                send_message_to_telegram(session, message)
                save_posted_story(story_id)
            time.sleep(1)  # Rate limiting

if __name__ == '__main__':
    main()
