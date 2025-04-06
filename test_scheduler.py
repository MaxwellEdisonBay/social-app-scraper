# test_scheduler.py
import os
import time
import logging
from datetime import datetime

import schedule

from scrapers.test_scraper import TestScraper
from handlers.news_queue import NewsQueue
from handlers.db_handler import DatabaseHandler
from handlers.ml_handler import mock_get_relevant_posts

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
            
            # Fetch full text for each relevant post using the corresponding scraper
            for post in processed_posts:
                if post.url in relevant_urls:
                    logger.info(f"Fetching full text for relevant post: {post.title}")
                    
                    # For test scheduler, we only have the test scraper
                    try:
                        full_text = test_scraper.fetch_post_full_text(post.url)
                        if full_text:
                            logger.info(f"Successfully fetched full text for {post.title} (length: {len(full_text)} characters)")
                            # Store the full text in the post object for future use
                            post.full_text = full_text
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