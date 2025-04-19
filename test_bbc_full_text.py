from scrapers.bbc_scraper import BBCScraper

def test_fetch_post_full_text():
    # Initialize the BBC scraper
    scraper = BBCScraper(enable_caching=False)
    
    # Test URLs with different wait times
    test_urls = [
        ("https://www.bbc.com/news/articles/c8073jzr1xko", 3.0),  # Regular article with 3 seconds wait
        ("https://www.bbc.com/news/videos/cj45yl5dy42o", 5.0)    # Video article with 5 seconds wait
    ]
    
    # Test each URL
    for url, wait_time in test_urls:
        print(f"\n{'='*50}")
        print(f"Testing URL: {url}")
        print(f"{'='*50}")
        
        # Fetch the full text with the specified wait time
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

if __name__ == "__main__":
    test_fetch_post_full_text() 