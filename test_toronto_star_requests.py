#!/usr/bin/env python
import sys
import os
from scrapers.toronto_star_scraper import TorontoStarScraper

def test_article_scraping():
    """Test scraping a specific Toronto Star article using requests"""
    # URL of the article to test
    article_url = "https://www.thestar.com/politics/federal/sliding-in-the-polls-jagmeet-singh-fights-to-be-heard-as-voters-abandon-the-ndp/article_929c6d6a-ece5-4d2e-904e-5bc809cbd820.html"
    
    # Initialize the scraper
    scraper = TorontoStarScraper(enable_caching=False)
    
    try:
        # Fetch the full text
        print(f"Fetching article: {article_url}")
        text_content, image_url = scraper.fetch_post_full_text(article_url)
        
        # Check if we got content
        if text_content:
            print(f"\nSuccessfully extracted article text ({len(text_content)} characters)")
            print("\nFirst 500 characters of the article:")
            print("-" * 50)
            print(text_content[:500] + "..." if len(text_content) > 500 else text_content)
            print("-" * 50)
            
            if image_url:
                print(f"\nFound image URL: {image_url}")
            
            # Save the full text to a file for inspection
            with open("toronto_star_article_requests.txt", "w", encoding="utf-8") as f:
                f.write(text_content)
            print("\nFull article text saved to 'toronto_star_article_requests.txt'")
        else:
            print("\nFailed to extract article text")
            
    except Exception as e:
        print(f"\nError during scraping: {e}")

if __name__ == "__main__":
    test_article_scraping() 