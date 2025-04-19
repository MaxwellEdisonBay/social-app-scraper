from scrapers.ircc_scraper import IRCCScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ircc_article():
    """Test the IRCC scraper with a specific article URL"""
    logger.info("Starting IRCC Scraper Test")
    
    # Initialize the scraper
    scraper = IRCCScraper(enable_caching=False)
    
    # Test URL - IRCC news article about Francophone communities
    test_url = "https://www.canada.ca/en/immigration-refugees-citizenship/news/2025/03/the-government-of-canada-is-investing-more-than-93-million-to-support-francophone-minority-communities.html"
    
    logger.info(f"Testing fetch_post_full_text with URL: {test_url}")
    
    # Test fetching full text
    text_content, image_url = scraper.fetch_post_full_text(test_url)
    
    if text_content:
        logger.info(f"Successfully fetched text content ({len(text_content)} characters)")
        logger.info(f"Text content preview: {text_content[:500]}...")
    else:
        logger.error("Failed to fetch text content")
    
    if image_url:
        logger.info(f"Found image URL: {image_url}")
    else:
        logger.info("No image URL found (expected for IRCC articles)")
    
    logger.info("Test Complete")

if __name__ == "__main__":
    test_ircc_article() 