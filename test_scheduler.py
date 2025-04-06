# test_scheduler.py
import os
import time
import logging
from datetime import datetime

import schedule

from scrapers.test_scraper import TestScraper
from handlers.news_queue import NewsQueue
from handlers.db_handler import DatabaseHandler

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

def process_news_queue():
    """
    Process posts in the news queue.
    """
    logger.info("Starting news queue processing")
    try:
        # Get posts to process
        posts_to_process = news_queue.process_posts()
        
        if posts_to_process:
            logger.info(f"Processing {len(posts_to_process)} posts")
            
            # Process each post
            for post in posts_to_process:
                logger.info(f"Processing post: {post.title}")
                
                # Fetch full text for each post
                full_text = test_scraper.fetch_post_full_text(post.url)
                logger.info(f"  Full text length: {len(full_text)} characters")
                
            # Mark posts as processed
            news_queue.mark_as_processed(posts_to_process)
            logger.info(f"Marked {len(posts_to_process)} posts as processed")
        else:
            logger.info("No posts to process in the queue")
            
    except Exception as e:
        logger.error(f"Error processing news queue: {e}")

def run_test_scheduler():
    """
    Run the test scheduler with short intervals.
    """
    logger.info("Starting test scheduler")
    
    # Schedule jobs with short intervals for testing
    schedule.every(5).seconds.do(scrape_test_news)
    schedule.every(10).seconds.do(process_news_queue)
    
    # Run immediately on startup
    logger.info("Running initial scrape")
    scrape_test_news()
    
    logger.info("Running initial news queue processing")
    process_news_queue()
    
    # Main loop - run for 30 seconds then exit
    logger.info("Entering scheduler loop (will run for 30 seconds)")
    start_time = time.time()
    
    while time.time() - start_time < 30:  # 30 seconds
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            time.sleep(5)
    
    logger.info("Test scheduler completed")

if __name__ == "__main__":
    # Clear the database before testing
    try:
        if os.path.exists('news_queue.db'):
            os.remove('news_queue.db')
            logger.info("Cleared existing database")
    except Exception as e:
        logger.warning(f"Could not clear database: {e}")
    
    run_test_scheduler() 