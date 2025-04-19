#!/usr/bin/env python
"""
Test script for BBC scraper's fetch_post_full_text method.
This script tests the method with a specific URL and disables caching.
"""

import sys
import os
from scrapers.bbc_scraper import BBCScraper

def main():
    # URL to test
    test_url = "https://www.bbc.com/news/videos/cj45yl5dy42o"
    
    # Create a BBC scraper instance with caching disabled
    scraper = BBCScraper(enable_caching=False)
    
    print(f"Testing fetch_post_full_text for URL: {test_url}")
    print("Caching is disabled for this test.")
    
    # Call the fetch_post_full_text method
    text_content, image_url = scraper.fetch_post_full_text(test_url)
    
    # Print the results
    print("\n" + "="*50)
    print("RESULTS:")
    print("="*50)
    
    if text_content:
        print(f"\nText content ({len(text_content)} characters):")
        print("-"*50)
        print(text_content)
        print("-"*50)
    else:
        print("\nNo text content was retrieved.")
    
    if image_url:
        print(f"\nImage URL: {image_url}")
    else:
        print("\nNo image URL was retrieved.")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main() 