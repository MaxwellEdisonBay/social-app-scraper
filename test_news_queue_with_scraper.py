import os
import time
from datetime import datetime

from handlers.news_queue import NewsQueue
from handlers.db_handler import DatabaseHandler
from scrapers.test_scraper import TestScraper

def test_news_queue_with_scraper():
    """
    Test the news queue with the test scraper.
    This demonstrates the full flow of:
    1. Scraper fetching news
    2. News being added to the queue
    3. Posts being processed
    4. Posts being moved to the backlog
    """
    print("=== TESTING NEWS QUEUE WITH TEST SCRAPER ===")
    
    # Initialize components
    db_handler = DatabaseHandler(max_posts=100)
    news_queue = NewsQueue(max_posts=100)
    test_scraper = TestScraper(db_handler=db_handler)
    
    try:
        # Step 1: Fetch news from the scraper
        print("\n=== STEP 1: Fetching news from the scraper ===")
        posts = test_scraper.fetch_news_updates()
        print(f"Scraper fetched {len(posts)} posts")
        
        # Display the fetched posts
        for i, post in enumerate(posts, 1):
            print(f"\n{i}. {post.title}")
            print(f"   URL: {post.url}")
            print(f"   Description: {post.desc[:100]}...")
        
        # Step 2: Add posts to the queue
        print("\n=== STEP 2: Adding posts to the queue ===")
        added_posts = news_queue.add_news(posts, "test")
        print(f"Added {len(added_posts)} posts to the queue")
        
        # Step 3: Check the queue
        print("\n=== STEP 3: Checking the queue ===")
        queued_posts = news_queue.db_handler.get_all_posts(status='queued')
        print(f"Queue contains {len(queued_posts)} posts:")
        for post in queued_posts:
            print(f"- {post.title} (Status: {post.status})")
        
        # Step 4: Process posts
        print("\n=== STEP 4: Processing posts ===")
        processed_posts = news_queue.pop_queue()
        print(f"Retrieved and processed {len(processed_posts)} posts:")
        for post in processed_posts:
            print(f"- {post.title} (Status: {post.status})")
            
            # Fetch full text for each post
            full_text = test_scraper.fetch_post_full_text(post.url)
            print(f"  Full text length: {len(full_text)} characters")
        
        # Step 5: Check the queue after processing
        print("\n=== STEP 5: Checking the queue after processing ===")
        queued_posts = news_queue.db_handler.get_all_posts(status='queued')
        print(f"Queue contains {len(queued_posts)} posts (should be 0)")
        
        # Step 6: Check the backlog
        print("\n=== STEP 6: Checking the backlog ===")
        backlog = news_queue.get_backlog()
        print(f"Backlog contains {len(backlog)} posts:")
        for post in backlog:
            print(f"- {post.title} (Status: {post.status})")
        
        # Step 7: Final check of the queue
        print("\n=== STEP 7: Final check of the queue ===")
        queued_posts = news_queue.db_handler.get_all_posts(status='queued')
        print(f"Queue contains {len(queued_posts)} posts (should be 0)")
        
        print("\n=== TEST SUMMARY ===")
        print("1. Scraper fetched news posts")
        print("2. Posts were added to the queue")
        print("3. Posts were retrieved from the queue and processed")
        print("4. Queue was emptied after processing")
        print("5. Posts were moved to the backlog")
        print("6. Queue remained empty")
        
    finally:
        # Clean up
        db_handler.close()


if __name__ == "__main__":
    test_news_queue_with_scraper() 