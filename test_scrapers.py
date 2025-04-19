from scrapers.bbc_scraper import BBCScraper
from scrapers.toronto_star_scraper import TorontoStarScraper
from scrapers.ircc_scraper import IRCCScraper

def test_scrapers():
    # Test BBC Scraper
    print("\n" + "="*50)
    print("Testing BBC Scraper")
    print("="*50)
    bbc_scraper = BBCScraper(enable_caching=False)
    bbc_posts = bbc_scraper.fetch_post_updates()
    print(f"Found {len(bbc_posts)} BBC posts")
    
    if bbc_posts:
        # Test the first post
        post = bbc_posts[0]
        print(f"\nTesting BBC post: {post.title}")
        print(f"URL: {post.url}")
        print(f"Image URL: {post.image_url}")
        
        # Test fetch_post_full_text
        text, image = bbc_scraper.fetch_post_full_text(post.url)
        print(f"Full text length: {len(text) if text else 0} characters")
        print(f"Image URL from fetch_post_full_text: {image}")
    
    # Test Toronto Star Scraper
    print("\n" + "="*50)
    print("Testing Toronto Star Scraper")
    print("="*50)
    ts_scraper = TorontoStarScraper(enable_caching=False)
    ts_posts = ts_scraper.fetch_post_updates()
    print(f"Found {len(ts_posts)} Toronto Star posts")
    
    if ts_posts:
        # Test the first post
        post = ts_posts[0]
        print(f"\nTesting Toronto Star post: {post.title}")
        print(f"URL: {post.url}")
        print(f"Image URL: {post.image_url}")
        
        # Test fetch_post_full_text
        text, image = ts_scraper.fetch_post_full_text(post.url)
        print(f"Full text length: {len(text) if text else 0} characters")
        print(f"Image URL from fetch_post_full_text: {image}")
    
    # Test IRCC Scraper
    print("\n" + "="*50)
    print("Testing IRCC Scraper")
    print("="*50)
    ircc_scraper = IRCCScraper(enable_caching=False)
    ircc_posts = ircc_scraper.fetch_post_updates()
    print(f"Found {len(ircc_posts)} IRCC posts")
    
    if ircc_posts:
        # Test the first post
        post = ircc_posts[0]
        print(f"\nTesting IRCC post: {post.title}")
        print(f"URL: {post.url}")
        print(f"Image URL: {post.image_url}")
        
        # Test fetch_post_full_text
        text, image = ircc_scraper.fetch_post_full_text(post.url)
        print(f"Full text length: {len(text) if text else 0} characters")
        print(f"Image URL from fetch_post_full_text: {image}")

if __name__ == "__main__":
    test_scrapers() 