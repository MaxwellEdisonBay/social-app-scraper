from scrapers.bbc_scraper import BBCScraper

def test_bbc_article():
    # Initialize the BBC scraper
    scraper = BBCScraper(enable_caching=False)
    
    # Test URL
    test_url = "https://www.bbc.com/news/articles/c20xq5nd8jeo"
    print(f"\nTesting BBC scraper with article: {test_url}")
    
    # Fetch the article content
    text_content, image_url = scraper.fetch_post_full_text(test_url)
    
    # Print results
    if text_content:
        print("\n=== Article Text ===")
        print(f"Text length: {len(text_content)} characters")
        print("First 500 characters:")
        print(text_content[:500] + "...")
    else:
        print("\nNo text content found")
    
    if image_url:
        print("\n=== Image URL ===")
        print(image_url)
    else:
        print("\nNo image URL found")

if __name__ == "__main__":
    test_bbc_article() 