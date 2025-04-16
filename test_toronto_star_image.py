#!/usr/bin/env python
import sys
import os
import logging
from bs4 import BeautifulSoup
from scrapers.toronto_star_scraper import TorontoStarScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_toronto_star_image.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_toronto_star_image")

def test_image_extraction():
    """Test the image extraction logic with a sample HTML containing a base64 src and srcset"""
    # Sample HTML with an image that has a base64 src and a srcset
    sample_html = """
    <article class="tnt-asset-type-article">
        <h3 class="tnt-headline"><a href="/test-article">Test Article</a></h3>
        <p class="tnt-summary">Test description</p>
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAADCAQAAAAe/WZNAAAAEElEQVR42mM8U88ABowYDABAxQPltt5zqAAAAABJRU5ErkJggg==" 
             alt="Test Image" 
             class="img-responsive" 
             srcset="https://bloximages.chicago2.vip.townnews.com/thestar.com/content/tncms/assets/v3/editorial/d/7c/d7c8bf7c-27f3-5a78-84d4-50b55fb61842/67f003a641ce6.image.jpg?crop=1763%2C1175%2C0%2C0&amp;resize=150%2C100&amp;order=crop%2Cresize 150w, https://bloximages.chicago2.vip.townnews.com/thestar.com/content/tncms/assets/v3/editorial/d/7c/d7c8bf7c-27f3-5a78-84d4-50b55fb61842/67f003a641ce6.image.jpg?crop=1763%2C1175%2C0%2C0&amp;resize=200%2C133&amp;order=crop%2Cresize 200w, https://bloximages.chicago2.vip.townnews.com/thestar.com/content/tncms/assets/v3/editorial/d/7c/d7c8bf7c-27f3-5a78-84d4-50b55fb61842/67f003a641ce6.image.jpg?crop=1763%2C1175%2C0%2C0&amp;resize=300%2C200&amp;order=crop%2Cresize 300w, https://bloximages.chicago2.vip.townnews.com/thestar.com/content/tncms/assets/v3/editorial/d/7c/d7c8bf7c-27f3-5a78-84d4-50b55fb61842/67f003a641ce6.image.jpg?crop=1763%2C1175%2C0%2C0&amp;resize=1200%2C800&amp;order=crop%2Cresize 1200w">
    </article>
    """
    
    # Parse the HTML
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    # Find the article
    article = soup.find('article', class_='tnt-asset-type-article')
    if not article:
        logger.error("Could not find article element")
        return
    
    # Find the image
    img_elem = article.find('img', class_='img-responsive')
    if not img_elem:
        logger.error("Could not find image element")
        return
    
    # Check if src is a base64 image
    src = img_elem.get('src', '')
    is_base64 = src.startswith('data:image')
    logger.info(f"src is base64: {is_base64}")
    
    # Check if srcset exists
    srcset = img_elem.get('srcset', '')
    logger.info(f"srcset: {srcset}")
    
    # Extract the image URL using the same logic as in the scraper
    image_url = None
    
    # If src is a base64 image, prioritize srcset
    if is_base64:
        # Try to get the highest quality image from srcset
        if srcset:
            try:
                # Split srcset into individual URLs and find the highest resolution
                srcset_parts = [part.strip().split(" ") for part in srcset.split(",")]
                logger.info(f"Srcset parts: {srcset_parts}")
                
                # Filter out any malformed entries and extract width numbers
                valid_parts = []
                for parts in srcset_parts:
                    if len(parts) >= 2:
                        url = parts[0]
                        size_str = parts[1]
                        if size_str.endswith('w'):
                            try:
                                width = int(size_str.replace('w', ''))
                                valid_parts.append((url, width))
                                logger.info(f"Valid part: {url} - {width}w")
                            except ValueError:
                                logger.error(f"Could not parse width from {size_str}")
                
                if valid_parts:
                    # Sort by width and get the URL with the highest width
                    image_url = max(valid_parts, key=lambda x: x[1])[0]
                    logger.info(f"Selected highest quality image from srcset: {image_url}")
                else:
                    logger.error("No valid parts found in srcset")
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing srcset: {e}")
    
    # If still no image URL, try data-srcset
    if not image_url and img_elem.get('data-srcset'):
        srcset = img_elem.get('data-srcset')
        # Get the first URL from srcset
        if srcset:
            image_url = srcset.split(',')[0].split(' ')[0]
            logger.info(f"Selected image from data-srcset: {image_url}")
    
    # If still no image URL, try data-src
    if not image_url:
        image_url = img_elem.get('data-src')
        if image_url:
            logger.info(f"Selected image from data-src: {image_url}")
    
    # If still no image URL and src is not base64, use src
    if not image_url and not is_base64:
        image_url = src
        if image_url:
            logger.info(f"Selected image from src: {image_url}")
    
    # Verify that we got the highest resolution image from srcset
    expected_url = "https://bloximages.chicago2.vip.townnews.com/thestar.com/content/tncms/assets/v3/editorial/d/7c/d7c8bf7c-27f3-5a78-84d4-50b55fb61842/67f003a641ce6.image.jpg?crop=1763%2C1175%2C0%2C0&amp;resize=1200%2C800&amp;order=crop%2Cresize"
    
    # Normalize URLs by replacing &amp; with & for comparison
    normalized_expected = expected_url.replace('&amp;', '&')
    normalized_actual = image_url.replace('&amp;', '&')
    
    if normalized_actual == normalized_expected:
        logger.info("✅ Test passed: Correctly extracted the highest resolution image from srcset")
    else:
        logger.error(f"❌ Test failed: Expected {normalized_expected}, got {normalized_actual}")

if __name__ == "__main__":
    test_image_extraction() 