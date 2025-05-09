# schedule_script.py
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import asyncio

import schedule
from dotenv import load_dotenv

from handlers.db_handler import DatabaseHandler
from handlers.ml_handler import (get_article_translation, get_relevant_posts,
                                 mock_get_relevant_posts)
from handlers.news_queue import NewsQueue
from handlers.telegram_handler import TelegramHandler
from handlers.api_handler import APIHandler
from scrapers.bbc_scraper import BBCScraper
from scrapers.toronto_star_scraper import TorontoStarScraper
from scrapers.ircc_scraper import IRCCScraper

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduler")

# Initialize shared components
db_handler = DatabaseHandler(max_posts=1000)
news_queue = NewsQueue(max_posts=1000)
telegram_handler = TelegramHandler()
api_handler = APIHandler()

# Initialize scrapers
scrapers = {
    "bbc": BBCScraper(enable_caching=True, max_posts=100),
    "toronto_star": TorontoStarScraper(enable_caching=True, max_posts=100),
    "ircc": IRCCScraper(enable_caching=True, max_posts=100, cooldown=2.0)
}

# Configuration for scheduling
SCHEDULE_CONFIG = {
    "bbc": {
        "interval": 30,  # minutes
        "enabled": True
    },
    "toronto_star": {
        "interval": 30,  # minutes
        "enabled": True
    },
    "ircc": {
        "interval": 60,  # minutes - longer interval due to cooldown
        "enabled": True
    },
    "news_queue": {
        "interval": 10,  # minutes
        "enabled": True
    }
}

def scrape_news(source: str) -> None:
    """
    Fetch news from a specific scraper and add to the queue.
    
    Args:
        source (str): Source name (e.g., 'bbc')
    """
    if source not in scrapers:
        logger.error(f"Unknown source: {source}")
        return
        
    logger.info(f"Starting scrape for {source}")
    try:
        scraper = scrapers[source]
        posts = scraper.fetch_post_updates()
        
        if posts:
            logger.info(f"Fetched {len(posts)} posts from {source}")
            added_posts = news_queue.add_news(posts, source)
            logger.info(f"Added {len(added_posts)} posts to the queue from {source}")
        else:
            logger.info(f"No new posts fetched from {source}")
            
    except Exception as e:
        logger.error(f"Error scraping {source}: {e}")

async def process_news_queue():
    """Process the news queue and broadcast relevant posts."""
    try:
        # Get posts from the queue
        processed_posts = news_queue.pop_queue()
        
        if processed_posts:
            logger.info(f"Processing {len(processed_posts)} posts from the queue")
            
            # Get API key for ML processing
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("GOOGLE_API_KEY environment variable not set")
                return
            
            # Get relevant posts using ML - process all posts at once
            logger.info("Filtering posts for relevance using batch processing")
            if os.getenv("USE_MOCK_ML") == "true":
                # Use mock function for testing
                relevant_urls = mock_get_relevant_posts(processed_posts)
            else:
                # Use actual ML function with batch processing
                relevant_urls = get_relevant_posts(processed_posts, api_key)
            
            logger.info(f"Found {len(relevant_urls)} relevant posts")
            
            # Process each relevant post
            for post in processed_posts:
                if post.url not in relevant_urls:
                    logger.info(f"Post not relevant, skipping: {post.title}")
                    continue
                
                try:
                    # Get the corresponding scraper based on the post's source
                    if post.source in scrapers:
                        scraper = scrapers[post.source]
                        
                        # Fetch full text if not already present
                        if not post.full_text:
                            logger.info(f"Fetching full text for: {post.title}")
                            full_text, image_url = scraper.fetch_post_full_text(post.url)
                            post.full_text = full_text
                            if image_url:  # Update image URL if one was found
                                post.image_url = image_url
                            news_queue.db_handler.update_post(post)
                        
                        # Get translations with cooldown to respect API limits
                        logger.info(f"Getting translations for: {post.title}")
                        
                        # Add a small cooldown between translation calls
                        time.sleep(1.5)  # 1.5 second cooldown between translation calls
                        
                        uk_title, en_title, en_text, uk_text = get_article_translation(
                            api_key, post.title, post.full_text
                        )
                        
                        if uk_title and en_title and en_text and uk_text:
                            # Map the translated fields to the post object
                            post.uk_title = uk_title
                            post.en_title = en_title
                            post.en_text = en_text
                            post.uk_text = uk_text
                            
                            # If post.desc is missing, use english_text as a fallback
                            if not post.desc:
                                logger.info(f"Using English text as description for: {post.title}")
                                post.desc = en_text
                                
                            news_queue.db_handler.update_post(post)
                            
                            # Send to news service API first
                            logger.info(f"Sending post to news service: {post.title}")
                            api_result = api_handler.add_post(post)
                            if api_result:
                                logger.info(f"Successfully sent post to news service: {post.title}")
                                # Get the news service URL from the API response
                                if isinstance(api_result, dict) and 'insertedPosts' in api_result and len(api_result['insertedPosts']) > 0:
                                    # Get the post data from the API response
                                    post_data = api_result['insertedPosts'][0]
                                    
                                    # Try to get the slug or _id from the response
                                    post_id = post_data.get('_id') or post_data.get('slug')
                                    
                                    if post_id:
                                        # Construct the URL using the NEWS_SERVICE_BASE_URL
                                        news_service_url = f"{api_handler.base_url}/uk/news/{post_id}"
                                        logger.info(f"Generated news service URL: {news_service_url}")
                                        
                                        # Send to Telegram subscribers with the news service URL
                                        logger.info(f"Sending post to Telegram subscribers: {post.title}")
                                        sent_count = await telegram_handler.broadcast_post(post, source=post.source, override_url=news_service_url)
                                        logger.info(f"Broadcasted post to {sent_count} subscribers")
                                    else:
                                        logger.warning(f"Could not find _id or slug in API response for post: {post.title}")
                                else:
                                    logger.warning(f"Unexpected API response format for post: {post.title}")
                            else:
                                logger.error(f"Failed to send post to news service: {post.title}")
                        else:
                            logger.error(f"Failed to get translations for: {post.title}")
                    else:
                        logger.warning(f"No scraper found for source '{post.source}', skipping: {post.title}")
                    
                except Exception as e:
                    logger.error(f"Error processing post {post.title}: {e}")
                    continue
            
            # All posts have been processed and moved to backlog
            logger.info(f"All {len(processed_posts)} posts have been processed")
        else:
            logger.info("No posts to process in the queue")
            
    except Exception as e:
        logger.error(f"Error in process_news_queue: {e}")

def setup_schedules() -> None:
    """
    Set up all scheduled jobs based on configuration.
    """
    # Set up scraper jobs
    for source, config in SCHEDULE_CONFIG.items():
        if source == "news_queue":
            continue  # Skip news queue here, it's handled in run_scheduler
            
        if config["enabled"]:
            interval = config["interval"]
            logger.info(f"Scheduling {source} scraper to run every {interval} minutes")
            schedule.every(interval).minutes.do(scrape_news, source=source)

def run_scheduler() -> None:
    """
    Run the scheduler loop.
    """
    logger.info("Starting scheduler")
    setup_schedules()
    
    # Create a wrapper function for the async process_news_queue
    def run_process_news_queue():
        asyncio.run(process_news_queue())
    
    # Update the scheduler to use the wrapper function
    if SCHEDULE_CONFIG["news_queue"]["enabled"]:
        interval = SCHEDULE_CONFIG["news_queue"]["interval"]
        logger.info(f"Scheduling news queue processing to run every {interval} minutes")
        schedule.every(interval).minutes.do(run_process_news_queue)
    
    # Run immediately on startup
    logger.info("Running initial scrape for all sources")
    for source in scrapers.keys():
        if SCHEDULE_CONFIG[source]["enabled"]:
            scrape_news(source)
    
    logger.info("Running initial news queue processing")
    run_process_news_queue()
    
    # Main loop
    logger.info("Entering scheduler loop")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    run_scheduler()
