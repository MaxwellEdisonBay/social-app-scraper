import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional, Dict, Tuple, Any
import logging
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from common.models.models import Post
from scrapers.base_scraper import BaseScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IRCCScraper(BaseScraper):
    def __init__(self, enable_caching: bool = True, max_posts: int = 1000, cooldown: float = 2.0):
        super().__init__(enable_caching, max_posts)
        self.base_url = "https://www.canada.ca/en"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Cooldown settings
        self.cooldown = cooldown
        self.last_request_time = 0
        
        # Create a session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,  # increased retries
            backoff_factor=2,  # increased backoff
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(self.headers)

    def _enforce_cooldown(self):
        """
        Enforce a cooldown period between requests to avoid rate limiting.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.cooldown:
            sleep_time = self.cooldown - time_since_last_request
            logger.info(f"Enforcing cooldown: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def _make_request(self, url: str, timeout: int = 60) -> Optional[requests.Response]:
        """
        Make a request with retry logic and error handling.
        
        Args:
            url (str): URL to request
            timeout (int): Request timeout in seconds
            
        Returns:
            Optional[requests.Response]: Response object if successful, None if failed
        """
        try:
            # Enforce cooldown between requests
            self._enforce_cooldown()
            
            # Add a small random delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            logger.info(f"Making request to {url}")
            
            # Split timeout into connect and read timeouts
            response = self.session.get(
                url, 
                timeout=(10, timeout),  # (connect timeout, read timeout)
                verify=True,  # Enable SSL verification
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Log response status and content length
            logger.info(f"Response status: {response.status_code}, Content length: {len(response.text)}")
            
            return response
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {url}: {e}")
            # Try with a longer timeout on the next retry
            if "read timeout" in str(e).lower():
                logger.info("Read timeout occurred, will retry with longer timeout")
            return None
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL error for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None

    def _get_latest_news(self) -> List[Post]:
        """
        Scrapes the latest news from the IRCC news page.
        
        Returns:
            List[Post]: List of posts from IRCC
        """
        try:
            news_list_endpoint = "/news/advanced-news-search/news-results.html?typ=newsreleases&dprtmnt=departmentofcitizenshipandimmigration&start=2015-01-01&end="
            full_url = self.base_url + news_list_endpoint
            
            response = self._make_request(full_url)
            if not response:
                logger.error("Failed to fetch news list page")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article elements with class 'item'
            articles = soup.find_all('article', class_='item')
            logger.info(f"Found {len(articles)} articles with class 'item'")
            
            posts = []
            
            for article in articles:
                try:
                    # Find the link directly within h3.h5
                    link = article.select_one('h3.h5 a')
                    if not link:
                        logger.warning("Article missing title link")
                        continue
                    
                    # Extract URL and title
                    url = link.get('href', '')
                    title = link.get_text().strip()
                    
                    if not url or not title:
                        logger.warning(f"Article missing URL or title: {url=}, {title=}")
                        continue
                    
                    # Extract timestamp
                    time_elem = article.find('time')
                    created_at = None
                    if time_elem and time_elem.get('datetime'):
                        try:
                            created_at = datetime.fromisoformat(time_elem['datetime'])
                        except (ValueError, AttributeError) as e:
                            logger.warning(f"Failed to parse datetime: {e}")
                    
                    # Extract description (the second paragraph, after the time paragraph)
                    paragraphs = article.find_all('p')
                    desc = ""
                    if len(paragraphs) > 1:  # We have more than just the time paragraph
                        desc = paragraphs[-1].get_text().strip()  # Get the last paragraph
                    
                    # Create Post object
                    post = Post(
                        title=title,
                        desc=desc,
                        url=url,
                        image_url=None,  # IRCC news doesn't have images
                        created_at=created_at,
                        source='ircc'
                    )
                    
                    posts.append(post)
                    logger.info(f"Found article: {title} - {url}")
                    
                except Exception as e:
                    logger.error(f"Error parsing article: {e}")
                    continue
            
            logger.info(f"Total posts found: {len(posts)}")
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching IRCC news: {e}")
            return []

    def fetch_post_full_text(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Scrapes the full text content of an IRCC news article.
        
        Args:
            url (str): The URL of the article to scrape
            
        Returns:
            Tuple[Optional[str], Optional[str]]: The article text and image URL if successful, None if failed
        """
        try:
            response = self._make_request(url)
            if not response:
                logger.error("Failed to fetch article page")
                return None, None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the main content - try multiple selectors
            article_content = None
            content_selectors = [
                ('div', {'id': 'news-release-container'}),  # Primary selector
                ('div', {'role': 'main'}),  # Fallback selector
                ('article', {'class': 'news-release'})  # Another possible selector
            ]
            
            for tag, attrs in content_selectors:
                article_content = soup.find(tag, attrs)
                if article_content:
                    logger.info(f"Found content using selector: {tag}, {attrs}")
                    break
            
            if not article_content:
                logger.error("Could not find main content")
                return None, None
            
            # Extract all relevant text elements
            text_elements = []
            
            # Get the title
            title = article_content.find('h1')
            if title:
                text_elements.append(title.get_text().strip())
            
            # Get the date and location
            date_location = article_content.find('div', class_='cmp-text')
            if date_location:
                text_elements.append(date_location.get_text().strip())
            
            # Get all paragraphs, excluding certain sections
            skip_sections = ['Associated links', 'Contacts']
            current_section = None
            
            for element in article_content.find_all(['p', 'h2', 'li']):
                # Check if this is a section header
                if element.name == 'h2':
                    current_section = element.get_text().strip()
                    if current_section not in skip_sections:
                        text_elements.append(current_section)
                    continue
                
                # Skip elements in excluded sections
                if current_section in skip_sections:
                    continue
                
                # Skip elements with certain classes
                skip_classes = ['visually-hidden', 'sr-only', 'hidden', 'gc-byline']
                if any(cls in element.get('class', []) for cls in skip_classes):
                    continue
                
                text = element.get_text().strip()
                if text:
                    text_elements.append(text)
            
            if not text_elements:
                logger.error("No text content found")
                return None, None
            
            final_text = '\n\n'.join(text_elements)
            logger.info(f"Successfully extracted {len(final_text)} characters of text")
            
            # IRCC articles don't have images
            return final_text, None
            
        except Exception as e:
            logger.error(f"Error fetching article: {e}")
            return None, None 
