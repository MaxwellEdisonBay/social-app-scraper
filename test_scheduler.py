# test_scheduler.py
import os
import time
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

import schedule

from scrapers.test_scraper import TestScraper
from handlers.news_queue import NewsQueue
from handlers.db_handler import DatabaseHandler
from handlers.ml_handler import mock_get_relevant_posts
from handlers.telegram_handler import TelegramHandler

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_scheduler")

# Initialize components
db_handler = DatabaseHandler(max_posts=100)
news_queue = NewsQueue(max_posts=100)
test_scraper = TestScraper(db_handler=db_handler)

# Initialize Telegram handler
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
logger.info(f"Bot token loaded: {'Yes' if bot_token else 'No'}")
telegram_handler = TelegramHandler()
logger.info(f"Bot enabled: {'Yes' if telegram_handler.enabled else 'No'}")

def scrape_test_news():
    """
    Fetch news from the test scraper and add to the queue.
    """
    logger.info("Starting scrape for test scraper")
    try:
        posts = test_scraper.fetch_news_updates()
        
        if posts:
            logger.info(f"Fetched {len(posts)} posts from test scraper")
            added_posts = news_queue.add_news(posts, "test")
            logger.info(f"Added {len(added_posts)} posts to the queue from test scraper")
        else:
            logger.info("No new posts fetched from test scraper")
            
    except Exception as e:
        logger.error(f"Error scraping test scraper: {e}")

async def process_news_queue():
    """
    Process posts in the news queue.
    """
    logger.info("Starting news queue processing")
    try:
        # Get posts to process and mark them as processed
        processed_posts = news_queue.pop_queue()
        
        if processed_posts:
            logger.info(f"Retrieved {len(processed_posts)} posts from the queue")
            
            # Set the source field for each post based on the source from the database
            for post in processed_posts:
                # Get the source from the database
                source = news_queue.db_handler.get_post_source(post.url)
                if source:
                    post.source = source
                    logger.info(f"Set source '{source}' for post: {post.title}")
                else:
                    logger.warning(f"Could not find source for post: {post.title}")
            
            # Use mock function to filter relevant posts (no API key needed)
            logger.info("Filtering posts using mock ML function for relevance")
            relevant_urls = mock_get_relevant_posts(processed_posts)
            
            # Log the results
            logger.info(f"Found {len(relevant_urls)} relevant posts out of {len(processed_posts)} total posts")
            
            # Process each post
            for post in processed_posts:
                try:
                    # Get the full text for the post
                    logger.info(f"Fetching full text for post: {post.title}")
                    full_text = test_scraper.fetch_post_full_text(post.url)
                    
                    if full_text:
                        logger.info(f"Successfully fetched full text for {post.title} (length: {len(full_text)})")
                        post.full_text = full_text
                        
                        # Create mock translations for testing
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        post.ukrainian_title = f"Тестовий пост з перекладами - {timestamp}"
                        post.english_summary = f"This is an improved English summary of the test post. It contains the main points of the article in a more readable format. This is test {timestamp}."
                        post.ukrainian_summary = f"Це покращений український переклад тестового поста. Він містить основні моменти статті в більш читабельному форматі. Це тест {timestamp}."
                        
                        # Update the post in the database
                        news_queue.db_handler.update_post(post)
                        logger.info(f"Updated post in database with translations: {post.title}")
                        
                        # Send the post to Telegram subscribers
                        if telegram_handler.enabled:
                            logger.info(f"Sending post to Telegram subscribers: {post.title}")
                            sent_count = await telegram_handler.broadcast_post(post, source=post.source)
                            logger.info(f"Sent post to {sent_count} Telegram subscribers")
                        else:
                            logger.warning("Telegram bot is not enabled. Please check your TELEGRAM_BOT_TOKEN.")
                    else:
                        logger.warning(f"Failed to fetch full text for {post.title}")
                except Exception as e:
                    logger.error(f"Error fetching full text for {post.title}: {e}")
            
            # For now, we're leaving the filtered list unused for future processing
            # In the future, we would process only the relevant posts
            
            logger.info(f"All {len(processed_posts)} posts have been moved to the backlog")
        else:
            logger.info("No posts to process in the queue")
            
    except Exception as e:
        logger.error(f"Error processing news queue: {e}")

def setup_schedules():
    """
    Set up all scheduled jobs.
    """
    # Schedule test scraper to run every 5 minutes
    schedule.every(5).minutes.do(scrape_test_news)
    
    # Schedule news queue processing to run every 5 minutes
    schedule.every(5).minutes.do(lambda: asyncio.run(process_news_queue()))

def run_scheduler():
    """
    Run the scheduler loop.
    """
    logger.info("Starting test scheduler")
    
    # Run immediately on startup
    logger.info("Running initial scrape")
    scrape_test_news()
    
    logger.info("Running initial news queue processing")
    asyncio.run(process_news_queue())
    
    # Set up schedules
    setup_schedules()
    
    # Run for 30 seconds
    logger.info("Entering scheduler loop (will run for 30 seconds)")
    start_time = time.time()
    while time.time() - start_time < 30:
        schedule.run_pending()
        time.sleep(1)
    
    logger.info("Test scheduler completed")

if __name__ == "__main__":
    run_scheduler() 