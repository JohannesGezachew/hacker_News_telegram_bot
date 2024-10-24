import requests
import urllib.parse
import logging
import time
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, HN_API_URL, HN_ITEM_URL, READABILITY_API_URL, POSTED_STORIES_FILE
from typing import Tuple, Optional, Set, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HackerNewsBot:
    def __init__(self):
        self.session = requests.Session()
        self.posted_stories = self.load_posted_stories()

    def fetch_top_stories(self) -> List[int]:
        """Fetch the top stories from Hacker News API."""
        try:
            response = self.session.get(HN_API_URL)
            response.raise_for_status()
            return response.json()[:30]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch top stories: {e}")
            return []

    def load_posted_stories(self) -> Set[str]:
        """Load the IDs of stories that have already been posted."""
        try:
            with open(POSTED_STORIES_FILE, 'r') as file:
                posted_stories = set(file.read().splitlines())
            logger.info(f"Loaded {len(posted_stories)} posted story IDs from file")
            return posted_stories
        except FileNotFoundError:
            logger.info("Posted stories file not found. Starting with an empty set.")
            return set()

    def save_posted_story(self, story_id: int) -> None:
        """Save the ID of a posted story to prevent reposting."""
        with open(POSTED_STORIES_FILE, 'a') as file:
            file.write(f'{story_id}\n')
        self.posted_stories.add(str(story_id))
        logger.info(f"Saved story ID {story_id} to posted stories file")

    def generate_instant_view_url(self, hn_item_id: int) -> Tuple[Optional[str], Optional[str]]:
        """Generate the Instant View URL for a Hacker News story."""
        try:
            hn_item_response = self.session.get(HN_ITEM_URL.format(hn_item_id))
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

    def send_message_to_telegram(self, message: str) -> None:
        """Send a message to the Telegram channel."""
        data = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = self.session.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage', json=data)
            response.raise_for_status()
            logger.info(f"Message sent to Telegram: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message to Telegram: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.content}")
            logger.error(f"Request data: {data}")

    def run(self):
        while True:
            try:
                top_stories = self.fetch_top_stories()
                stories_posted = 0

                for story_id in top_stories:
                    if str(story_id) not in self.posted_stories:
                        iv_url, article_url = self.generate_instant_view_url(story_id)
                        if iv_url:
                            message = (
                                f'<a href="{iv_url}">Read full article (Instant View)</a>\n'
                                f'Original article: <a href="{article_url}">{article_url}</a>\n'
                                f'Comments: <a href="https://news.ycombinator.com/item?id={story_id}">Hacker News Comments</a>'
                            )
                            self.send_message_to_telegram(message)
                            self.save_posted_story(story_id)
                            stories_posted += 1
                            logger.info(f"Posted story {story_id}. Total stories posted this run: {stories_posted}")

                            if stories_posted >= 5:  # Post exactly 5 stories per run
                                break

                            time.sleep(60)  # Wait 1 minute between posts within the same run

                logger.info(f"Posted {stories_posted} stories. Waiting for next run...")
                time.sleep(10800)  # Wait for 3 hours (3 * 60 * 60 seconds) before the next run

            except Exception as e:
                logger.error(f"An error occurred during the run: {e}")
                time.sleep(300)  # Wait for 5 minutes before trying again

def main():
    bot = HackerNewsBot()
    bot.run()

if __name__ == '__main__':
    main()
