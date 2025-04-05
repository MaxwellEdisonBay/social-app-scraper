import time
from datetime import datetime

from scrapers.bbc_scraper import BBCScraper


def test_bbc_scraper():
    print("Starting BBC Scraper Test")
    print("=" * 50)
    
    # Initialize scraper with caching enabled
    scraper = BBCScraper(enable_caching=True, max_posts=100)
    
    
    # Test 1: First fetch - should get all posts
    print("\nTest 1: First Fetch")
    print("-" * 30)
    new_posts = scraper.fetch_post_updates()
    print(f"Found {len(new_posts)} new posts")
     
    if new_posts:
        print("\nSample post details:")
        post = new_posts[0]
        print(f"Title: {post.title}")
        print(f"URL: {post.url}")
        print(f"Description: {post.desc}")
        print(f"Created at: {post.created_at}")
        
        # Get full text for the first post
        print("\nFetching full text...")
        full_text = scraper.fetch_post_full_text(post.url)
        if full_text:
            print(f"Full text preview: {full_text[:200]}...")
    
    # Test 2: Immediate second fetch - should get no new posts
    print("\nTest 2: Immediate Second Fetch")
    print("-" * 30)
    new_posts = scraper.fetch_post_updates()
    print(f"Found {len(new_posts)} new posts (should be 0)")
    
    # Test 3: Wait and fetch again - might get new posts
    print("\nTest 3: Delayed Fetch")  
    print("-" * 30)
    print("Waiting 10 seconds before fetching again...")
    time.sleep(10)
    new_posts = scraper.fetch_post_updates()
    print(f"Found {len(new_posts)} new posts")
    
    if new_posts:
        print("\nNew post details:")
        post = new_posts[0]
        print(f"Title: {post.title}")
        print(f"URL: {post.url}")
        print(f"Description: {post.desc}")
        print(f"Created at: {post.created_at}")
    
    # Test 4: Verify full text fetching
    print("\nTest 4: Full Text Fetching")
    print("-" * 30)
    if new_posts:
        post = new_posts[0]
        print(f"Fetching full text for: {post.title}")
        full_text = scraper.fetch_post_full_text(post.url)
        if full_text:
            print(f"Successfully fetched full text ({len(full_text)} characters)")
            print(f"Preview: {full_text[:200]}...")
        else:
            print("Failed to fetch full text")
    
    print("\nTest Complete")
    print("=" * 50)


if __name__ == "__main__":
    test_bbc_scraper() 