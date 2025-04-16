from scrapers.bbc_scraper import BBCScraper
import re

def test_bbc_scraper():
    print("Testing BBC Scraper...")
    scraper = BBCScraper(enable_caching=False)
    
    print("Fetching latest news...")
    posts = scraper._get_latest_news()
    
    print(f"\nFound {len(posts)} posts:")
    
    # Look for video posts
    video_posts = [post for post in posts if "video" in post.url.lower()]
    print(f"\nFound {len(video_posts)} video posts:")
    
    for i, post in enumerate(video_posts[:3]):
        print(f"\nVideo Post {i+1}:")
        print(f"Title: {post.title}")
        print(f"URL: {post.url}")
        print(f"Image URL: {post.image_url}")
        print(f"Description: {post.desc}")
        print("-" * 80)
    
    # Print a few regular posts for comparison
    regular_posts = [post for post in posts if "video" not in post.url.lower()]
    print(f"\nSample of {min(3, len(regular_posts))} regular posts:")
    
    for i, post in enumerate(regular_posts[:3]):
        print(f"\nRegular Post {i+1}:")
        print(f"Title: {post.title}")
        print(f"URL: {post.url}")
        print(f"Image URL: {post.image_url}")
        print(f"Description: {post.desc}")
        print("-" * 80)

if __name__ == "__main__":
    test_bbc_scraper() 