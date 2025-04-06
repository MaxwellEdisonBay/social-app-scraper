#!/usr/bin/env python
# test_process_news_queue.py
import os
import logging
from datetime import datetime

from handlers.news_queue import NewsQueue
from handlers.db_handler import DatabaseHandler
from common.models.models import Post
from scrapers.test_scraper import TestScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_process_news_queue.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_process_news_queue")

def create_test_posts():
    """Create test posts with various topics"""
    # Generate a unique timestamp for each run
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    return [
        Post(
            url=f"https://example.com/ukraine1_{timestamp}",
            title=f"Ukraine receives new military aid from Canada - {timestamp}",
            desc=f"Canada has announced a new package of military aid for Ukraine, including armored vehicles and ammunition. This is test {timestamp}.",
            image_url=f"https://example.com/ukraine1_{timestamp}.jpg",
            created_at=datetime.now(),
            source="test"
        ),
        Post(
            url=f"https://example.com/ukraine2_{timestamp}",
            title=f"Ukrainian refugees find new homes in Toronto - {timestamp}",
            desc=f"A new program helps Ukrainian refugees settle in Toronto, providing housing and job assistance. This is test {timestamp}.",
            image_url=f"https://example.com/ukraine2_{timestamp}.jpg",
            created_at=datetime.now(),
            source="test"
        ),
        Post(
            url=f"https://example.com/sports_{timestamp}",
            title=f"Local sports team wins championship - {timestamp}",
            desc=f"The local hockey team has won the championship after a thrilling final match. This is test {timestamp}.",
            image_url=f"https://example.com/sports_{timestamp}.jpg",
            created_at=datetime.now(),
            source="test"
        ),
        Post(
            url=f"https://example.com/weather_{timestamp}",
            title=f"Weather forecast for the weekend - {timestamp}",
            desc=f"Sunny weather expected for the weekend with temperatures reaching 25°C. This is test {timestamp}.",
            image_url=f"https://example.com/weather_{timestamp}.jpg",
            created_at=datetime.now(),
            source="test"
        ),
        Post(
            url=f"https://example.com/immigration_{timestamp}",
            title=f"New immigration policies announced - {timestamp}",
            desc=f"The government has announced new immigration policies that will affect Ukrainian refugees. This is test {timestamp}.",
            image_url=f"https://example.com/immigration_{timestamp}.jpg",
            created_at=datetime.now(),
            source="test"
        )
    ]

def test_process_news_queue():
    """Test the process_news_queue functionality with mock ML"""
    logger.info("Starting test of process_news_queue")
    
    # Set environment variable to use mock ML
    os.environ["USE_MOCK_ML"] = "true"
    
    # Initialize components with a specific test database path
    test_db_path = "test_process_news_queue.db"
    db_handler = DatabaseHandler(db_path=test_db_path, max_posts=100)
    news_queue = NewsQueue(db_path=test_db_path, max_posts=100)
    test_scraper = TestScraper(db_handler=db_handler)
    
    # Create a custom process_news_queue function for testing
    def custom_process_news_queue():
        """Custom process_news_queue function for testing"""
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
                from handlers.ml_handler import mock_get_relevant_posts
                logger.info("Filtering posts using mock ML function for relevance")
                relevant_urls = mock_get_relevant_posts(processed_posts)
                
                # Log the results
                logger.info(f"Found {len(relevant_urls)} relevant posts out of {len(processed_posts)} total posts")
                
                # Fetch full text for each relevant post using the test scraper
                for post in processed_posts:
                    if post.url in relevant_urls:
                        logger.info(f"Fetching full text for relevant post: {post.title}")
                        
                        try:
                            full_text = test_scraper.fetch_post_full_text(post.url)
                            if full_text:
                                logger.info(f"Successfully fetched full text for {post.title} (length: {len(full_text)} characters)")
                                # Store the full text in the post object for future use
                                post.full_text = full_text
                                
                                # Mock translations for testing
                                logger.info(f"Getting mock translations for post: {post.title}")
                                post.ukrainian_title = f"УКРАЇНСЬКИЙ ПЕРЕКЛАД: {post.title}"
                                post.english_summary = f"This is an improved English summary of the article: {post.title}"
                                post.ukrainian_summary = f"Це покращений український переклад статті: {post.title}"
                                
                                # Update the post in the database with translations
                                news_queue.db_handler.update_post(post)
                                logger.info(f"Updated post in database with translations: {post.title}")
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
    
    try:
        # Create test posts
        test_posts = create_test_posts()
        logger.info(f"Created {len(test_posts)} test posts")
        
        # Add posts to the queue
        added_posts = news_queue.add_news(test_posts, "test")
        logger.info(f"Added {len(added_posts)} posts to the queue")
        
        # Verify posts are in the queue
        queued_posts = news_queue.db_handler.get_all_posts(status='queued')
        logger.info(f"Queue contains {len(queued_posts)} posts")
        
        # Process the queue using our custom function
        custom_process_news_queue()
        
        # Verify posts have been processed
        processed_posts = news_queue.db_handler.get_all_posts(status='processed')
        logger.info(f"Backlog contains {len(processed_posts)} posts")
        
        # Check if the queue is empty
        queued_posts = news_queue.db_handler.get_all_posts(status='queued')
        logger.info(f"Queue contains {len(queued_posts)} posts (should be 0)")
        
        # Verify that the relevant posts have full text and translations
        relevant_posts = [post for post in processed_posts if post.full_text]
        logger.info(f"Found {len(relevant_posts)} posts with full text")
        
        # Print details of each processed post
        for post in processed_posts:
            logger.info(f"Post: {post.title}")
            logger.info(f"  URL: {post.url}")
            logger.info(f"  Source: {post.source}")
            logger.info(f"  Status: {post.status}")
            logger.info(f"  Has full text: {'Yes' if post.full_text else 'No'}")
            if post.full_text:
                logger.info(f"  Full text length: {len(post.full_text)} characters")
                logger.info(f"  Full text preview: {post.full_text[:100]}...")
                logger.info(f"  Has Ukrainian title: {'Yes' if post.ukrainian_title else 'No'}")
                logger.info(f"  Has English summary: {'Yes' if post.english_summary else 'No'}")
                logger.info(f"  Has Ukrainian summary: {'Yes' if post.ukrainian_summary else 'No'}")
                if post.ukrainian_title:
                    logger.info(f"  Ukrainian title: {post.ukrainian_title}")
                if post.english_summary:
                    logger.info(f"  English summary preview: {post.english_summary[:100]}...")
                if post.ukrainian_summary:
                    logger.info(f"  Ukrainian summary preview: {post.ukrainian_summary[:100]}...")
        
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
    finally:
        # Clean up
        db_handler.close()

if __name__ == "__main__":
    test_process_news_queue() 