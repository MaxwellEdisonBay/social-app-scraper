# schedule_script.py
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

import schedule

from scrapers.bbc_scraper import BBCScraper
from handlers.news_queue import NewsQueue
from handlers.db_handler import DatabaseHandler
from handlers.ml_handler import get_article_translation, get_relevant_posts, mock_get_relevant_posts

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
db_handler = DatabaseHandler(max_posts=100)
news_queue = NewsQueue(max_posts=100)

# Initialize scrapers
scrapers = {
    "bbc": BBCScraper(db_handler=db_handler)
}

# Configuration for scheduling
SCHEDULE_CONFIG = {
    "bbc": {
        "interval": 30,  # minutes
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
        posts = scraper.fetch_news_updates()
        
        if posts:
            logger.info(f"Fetched {len(posts)} posts from {source}")
            added_posts = news_queue.add_news(posts, source)
            logger.info(f"Added {len(added_posts)} posts to the queue from {source}")
        else:
            logger.info(f"No new posts fetched from {source}")
            
    except Exception as e:
        logger.error(f"Error scraping {source}: {e}")

def process_news_queue() -> None:
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
            
            # Check if we're in test mode
            use_mock = os.getenv("USE_MOCK_ML", "false").lower() == "true"
            
            if use_mock:
                # Use mock function to filter relevant posts (no API key needed)
                logger.info("Using mock ML function for relevance filtering (test mode)")
                relevant_urls = mock_get_relevant_posts(processed_posts)
            else:
                # Use Gemini to filter relevant posts
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    logger.error("GEMINI_API_KEY environment variable not set")
                    return
                    
                logger.info("Filtering posts using Gemini for relevance")
                relevant_urls = get_relevant_posts(processed_posts, api_key)
            
            # Log the results
            logger.info(f"Found {len(relevant_urls)} relevant posts out of {len(processed_posts)} total posts")
            
            # Fetch full text for each relevant post using the corresponding scraper
            for post in processed_posts:
                if post.url in relevant_urls:
                    logger.info(f"Fetching full text for relevant post: {post.title}")
                    
                    # Get the corresponding scraper based on the post's source
                    if post.source in scrapers:
                        scraper = scrapers[post.source]
                        try:
                            full_text = scraper.fetch_post_full_text(post.url)
                            if full_text:
                                logger.info(f"Successfully fetched full text for {post.title} (length: {len(full_text)} characters)")
                                # Store the full text in the post object for future use
                                post.full_text = full_text
                                
                                # Get translations if we have a Gemini API key
                                if not use_mock and api_key:
                                    logger.info(f"Getting translations for post: {post.title}")
                                    try:
                                        uk_title, en_text, uk_text = get_article_translation(
                                            api_key=api_key,
                                            title=post.title,
                                            text=full_text
                                        )
                                        
                                        if uk_title and en_text and uk_text:
                                            logger.info(f"Successfully translated post: {post.title}")
                                            # Update the post with translations
                                            post.ukrainian_title = uk_title
                                            post.english_summary = en_text
                                            post.ukrainian_summary = uk_text
                                            # Update the post in the database
                                            news_queue.db_handler.update_post(post)
                                            logger.info(f"Updated post in database with translations: {post.title}")
                                        else:
                                            logger.warning(f"Failed to get translations for post: {post.title}")
                                    except Exception as e:
                                        logger.error(f"Error getting translations for {post.title}: {e}")
                                else:
                                    logger.info(f"Skipping translations for post: {post.title} (test mode or no API key)")
                            else:
                                logger.warning(f"Failed to fetch full text for {post.title}")
                        except Exception as e:
                            logger.error(f"Error fetching full text for {post.title}: {e}")
                    else:
                        logger.warning(f"No scraper found for source '{post.source}', skipping full text fetch for {post.title}")
            
            # For now, we're leaving the filtered list unused for future processing
            # In the future, we would process only the relevant posts
            
            logger.info(f"All {len(processed_posts)} posts have been moved to the backlog")
        else:
            logger.info("No posts to process in the queue")
            
    except Exception as e:
        logger.error(f"Error processing news queue: {e}")

def setup_schedules() -> None:
    """
    Set up all scheduled jobs based on configuration.
    """
    # Set up scraper jobs
    for source, config in SCHEDULE_CONFIG.items():
        if source == "news_queue":
            continue  # Skip news queue here, handle it separately
            
        if config["enabled"]:
            interval = config["interval"]
            logger.info(f"Scheduling {source} scraper to run every {interval} minutes")
            schedule.every(interval).minutes.do(scrape_news, source=source)
    
    # Set up news queue processing job
    if SCHEDULE_CONFIG["news_queue"]["enabled"]:
        interval = SCHEDULE_CONFIG["news_queue"]["interval"]
        logger.info(f"Scheduling news queue processing to run every {interval} minutes")
        schedule.every(interval).minutes.do(process_news_queue)

def run_scheduler() -> None:
    """
    Run the scheduler loop.
    """
    logger.info("Starting scheduler")
    setup_schedules()
    
    # Run immediately on startup
    logger.info("Running initial scrape for all sources")
    for source in scrapers.keys():
        if SCHEDULE_CONFIG[source]["enabled"]:
            scrape_news(source)
    
    logger.info("Running initial news queue processing")
    process_news_queue()
    
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
