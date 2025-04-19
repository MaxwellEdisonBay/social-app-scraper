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

def test_fetch_post_full_text():
    # Initialize the BBC scraper
    scraper = BBCScraper(enable_caching=False)
    
    # Test URLs
    test_urls = [
        "https://www.bbc.com/news/articles/c8073jzr1xko",
        "https://www.bbc.com/news/videos/cj45yl5dy42o"
    ]
    
    # Test each URL
    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"Testing URL: {url}")
        print(f"{'='*50}")
        
        # Fetch the full text
        result = scraper.fetch_post_full_text(url)
        
        if result is None:
            print("Failed to fetch content. Result is None.")
            continue
            
        text_content, image_url = result
        
        # Print results
        if text_content:
            print(f"\nText content length: {len(text_content)} characters")
            print(f"Text content preview: {text_content[:200]}...")
        else:
            print("\nNo text content found")
            
        if image_url:
            print(f"\nImage URL: {image_url}")
        else:
            print("\nNo image URL found")

def test_article(url, article_type):
    print(f"\n{'='*50}")
    print(f"Testing {article_type} article: {url}")
    print(f"{'='*50}")
    
    scraper = BBCScraper(enable_caching=False)
    text_content, image_url = scraper.fetch_post_full_text(url)
    
    print(f"\nImage URL: {image_url}")
    print(f"\nText content length: {len(text_content)} characters")
    print(f"\nText content preview (first 500 chars):")
    print(f"{text_content[:500]}...")
    
    return text_content, image_url

if __name__ == "__main__":
    # Test video article
    video_url = "https://www.bbc.com/news/videos/c33zr4n8pm3o"
    video_text, video_image = test_article(video_url, "VIDEO")
    
    # Test regular article
    article_url = "https://www.bbc.com/news/articles/c20xq5nd8jeo"
    article_text, article_image = test_article(article_url, "REGULAR") 