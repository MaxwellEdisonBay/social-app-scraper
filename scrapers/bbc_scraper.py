import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional, Tuple
import time  # Add time module for sleep functionality
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from common.models.models import Post
from scrapers.base_scraper import BaseScraper

def get_shadow_root(driver, element):
        return driver.execute_script('return arguments[0].shadowRoot', element)

class BBCScraper(BaseScraper):
    def __init__(self, enable_caching: bool = True, max_posts: int = 1000):
        super().__init__(enable_caching, max_posts)
        self.base_url = "https://www.bbc.com/news/world/us_and_canada"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def _get_latest_news(self) -> List[Post]:
        """
        Crawls the BBC News US & Canada page and extracts the latest news articles.

        Returns:
            List[Post]: List of scraped posts
        """
        base_url = 'https://www.bbc.com'
        url = base_url + "/news/us-canada"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            articles = []
            article_elements = soup.find_all("div", {"data-testid": "dundee-card"},
                                             recursive=True)  # find all the promo divs that contain articles.

            for element in article_elements:
                print("\nProcessing article element...")
                
                link_el = element.find("a")
                title_el = element.find("h2", {"data-testid": "card-headline"})
                desc_el = element.find("p", {"data-testid": "card-description"})
                
                # Check if we have a valid link
                if link_el and link_el.get("href"):
                    article_url = base_url + link_el.get("href")
                    
                    # Create a post with basic information
                    post = Post(
                        url=article_url,
                        title=title_el.text.strip() if title_el else "No title available",
                        desc=desc_el.text.strip() if desc_el else "No description available",
                        image_url=None,  # Will be populated later by fetch_post_full_text
                        created_at=datetime.now(),
                        source='bbc'
                    )
                    
                    articles.append(post)
            
            return articles

        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    def _get_largest_image_src(self, srcset):
        """Extracts the URL of the largest image from a srcset string."""
        if not srcset:
            return None
        sources = srcset.strip().split(',')
        largest_url = None
        largest_width = -1
        for source in sources:
            parts = source.strip().split()
            if len(parts) == 2 and parts[1].endswith('w'):
                try:
                    width = int(parts[1][:-1])
                    if width > largest_width:
                        largest_width = width
                        largest_url = parts[0]
                except ValueError:
                    pass
            elif len(parts) == 1:
                largest_url = parts[0]
        return largest_url.strip() if largest_url else None

    def fetch_post_full_text(self, url: str) -> Tuple[str, Optional[str]]:
        """
        Scrapes the full text content of a BBC news article using Selenium.
        
        Args:
            url (str): The URL of the article to scrape
            
        Returns:
            Tuple[str, Optional[str]]: The article text and image URL if successful, None if failed
        """
        driver = None
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
            
            # Initialize the Chrome driver
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Navigate to the page
            print(f"Navigating to {url}")
            driver.get(url)
            
            # Wait for the page to load
            wait = WebDriverWait(driver, 15)
            
            # Initialize variables
            text_content = ""
            image_url = None
            
            # Check if this is a video article
            is_video_article = "videos" in url
            print(f"Is video article: {is_video_article}")
            
            if is_video_article:
                # For video articles, try to find the video content
                try:
                    # Wait for the video section to be present
                    wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="video-page-video-section"]'))
                    )
                    
                    # Try to find the video title
                    try:
                        # Try multiple selectors for the title
                        title_selectors = [
                            'h1.sc-6bafae19-2',  # New style
                            'h1.video-page-title',  # Alternative style
                            'div[data-testid="video-page-video-section"] h1',  # Generic h1 in video section
                            'h1'  # Fallback to any h1
                        ]
                        
                        for selector in title_selectors:
                            try:
                                title_element = driver.find_element(By.CSS_SELECTOR, selector)
                                if title_element:
                                    text_content += title_element.text.strip() + "\n\n"
                                    print(f"Found video title using selector {selector}: {title_element.text.strip()}")
                                    break
                            except:
                                continue
                    except Exception as e:
                        print(f"Error finding video title: {e}")
                    
                    # Try to find the video description
                    try:
                        # Try multiple selectors for the description
                        desc_selectors = [
                            'div.sc-6bafae19-3',  # New style
                            'div.video-page-description',  # Alternative style
                            'div[data-testid="video-page-video-section"] p',  # Any paragraph in video section
                            'div[data-component="text-block"]'  # Fallback to text block
                        ]
                        
                        for selector in desc_selectors:
                            try:
                                desc_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                if desc_elements:
                                    for element in desc_elements:
                                        text = element.text.strip()
                                        if text:
                                            text_content += text + "\n\n"
                                    print(f"Found video description using selector {selector}")
                                    break
                            except:
                                continue
                    except Exception as e:
                        print(f"Error finding video description: {e}")
                    
                    # Try to find the video image
                    try:
                        player_el = driver.find_element(By.ID, "toucan-bbcMediaPlayer0")
                        player_root = get_shadow_root(driver, player_el)
                        preplay_el = player_root.find_element(By.CSS_SELECTOR, 'smp-preplay-layout')
                        preplay_root = get_shadow_root(driver, preplay_el)
                        holding_image_el = preplay_root.find_element(By.CSS_SELECTOR, 'smp-holding-image')
                        holding_image_root = get_shadow_root(driver, holding_image_el)
                        img_el = holding_image_root.find_element(By.CSS_SELECTOR, 'img')
                        image_src_set = img_el.get_attribute('srcset')
                        if image_src_set:
                            image_url = self._get_largest_image_src(image_src_set)
                            if image_url:
                                print(f"Found video image with srcset: {image_url}")
                        else:
                            print("No image srcset found")
                    except Exception as e:
                        print(f"Error finding video image: {e}")
                    
                except Exception as e:
                    print(f"Error processing video article: {e}")
            else:
                # For regular articles, find all text blocks
                try:
                    # Wait for text content to be available
                    wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
                    )
                    
                    # Find the article title
                    title_element = driver.find_element(By.CSS_SELECTOR, 'h1')
                    if title_element:
                        text_content += title_element.text.strip() + "\n\n"
                    
                    # Find all paragraphs in the article
                    paragraphs = driver.find_elements(By.CSS_SELECTOR, 'article p')
                    for p in paragraphs:
                        text_content += p.text.strip() + "\n\n"
                    
                    # Try to find the main image
                    try:
                        # First try to find an image with srcset
                        img_elements = driver.find_elements(By.CSS_SELECTOR, 'article img')
                        for img in img_elements:
                            srcset = img.get_attribute('srcset')
                            if srcset:
                                image_url = self._get_largest_image_src(srcset)
                                if image_url:
                                    print(f"Found image with srcset: {image_url}")
                                    break
                        
                        # If no image found with srcset, try regular src
                        if not image_url:
                            for img in img_elements:
                                src = img.get_attribute('src')
                                if src and "placeholder" not in src.lower():
                                    image_url = src
                                    print(f"Found image with src: {image_url}")
                                    break
                    except Exception as e:
                        print(f"Error finding article image: {e}")
                    
                except Exception as e:
                    print(f"Error extracting article content: {e}")
            
            # If we still don't have an image, try one last method
            if not image_url:
                try:
                    # Try to find any image on the page
                    all_images = driver.find_elements(By.TAG_NAME, 'img')
                    for img in all_images:
                        src = img.get_attribute('src')
                        if src and "placeholder" not in src.lower() and "icon" not in src.lower():
                            image_url = src
                            print(f"Found fallback image: {image_url}")
                            break
                except Exception as e:
                    print(f"Error finding fallback image: {e}")
            
            return text_content, image_url
            
        except Exception as e:
            print(f"Error in fetch_post_full_text: {e}")
            return "", None
        finally:
            if driver:
                driver.quit()


if __name__ == "__main__":
    # Test the scraper
    scraper = BBCScraper(enable_caching=True, max_posts=100)
    
    # Test full text fetching with a specific article
    # test_url = "https://www.bbc.com/news/articles/c05np01y809o"
    test_url = "https://www.bbc.com/news/articles/c4grlzegewno"
    print(f"\nTesting full text fetch for article: {test_url}")
    full_text = scraper.fetch_post_full_text(test_url)
    if full_text:
        print(f"Successfully fetched full text ({len(full_text)} characters)")
        print(f"Preview: {full_text[:200]}...")
        print(full_text)
    else:
        print("Failed to fetch full text")
    
    print("\nFetching news updates...")
    new_posts = scraper.fetch_post_updates()
    
    print(f"\nFound {len(new_posts)} new posts:")
    for post in new_posts:
        print(f"\nTitle: {post.title}")
        print(f"URL: {post.url}")
        print(f"Description: {post.desc}")
        
        # Get full text for the first post as an example
        if new_posts and post == new_posts[0]:
            print("\nFetching full text for first post...")
            full_text = scraper.fetch_post_full_text(post.url)
            if full_text:
                print(f"Full text preview: {full_text[:200]}...")
