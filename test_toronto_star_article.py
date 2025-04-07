#!/usr/bin/env python
import sys
import os
import logging
from scrapers.toronto_star_scraper import TorontoStarScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_toronto_star_article.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_toronto_star_article")

def test_article_scraping():
    """Test scraping a specific Toronto Star article"""
    # URL of the article to test
    article_url = "https://www.thestar.com/sports/hockey/alex-ovechkin-breaks-wayne-gretzkys-nhl-career-goals-record-by-scoring-his-895th/article_57353e1b-276c-59f0-9d68-13ebd194114d.html"
    
    # Initialize the scraper
    scraper = TorontoStarScraper(enable_caching=False)
    
    # Fetch the full text
    logger.info(f"Fetching article: {article_url}")
    full_text = scraper.fetch_post_full_text(article_url)
    
    # Check if we got content
    if full_text:
        logger.info(f"Successfully extracted article text ({len(full_text)} characters)")
        logger.info("First 500 characters of the article:")
        logger.info("-" * 50)
        logger.info(full_text[:500] + "..." if len(full_text) > 500 else full_text)
        logger.info("-" * 50)
        
        # Save the full text to a file for inspection
        with open("toronto_star_article.txt", "w", encoding="utf-8") as f:
            f.write(full_text)
        logger.info("Full article text saved to 'toronto_star_article.txt'")
    else:
        logger.error("Failed to extract article text")

if __name__ == "__main__":
    test_article_scraping() 