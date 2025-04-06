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
        # Get posts to process
        posts_to_process = news_queue.process_posts()
        
        if posts_to_process:
            logger.info(f"Processing {len(posts_to_process)} posts")
            
            # Process each post (in a real implementation, this would do something with the posts)
            for post in posts_to_process:
                logger.info(f"Processing post: {post.title}")
                
                # Here you would add your processing logic
                # For example, fetching full text, translating, etc.
                
            # Mark posts as processed
            news_queue.mark_as_processed(posts_to_process)
            logger.info(f"Marked {len(posts_to_process)} posts as processed")
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
