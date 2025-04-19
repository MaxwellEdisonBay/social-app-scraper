import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional, Tuple
from common.models.models import Post
from scrapers.base_scraper import BaseScraper

class TorontoStarScraper(BaseScraper):
    def __init__(self, enable_caching: bool = True, max_posts: int = 1000):
        super().__init__(enable_caching, max_posts)
        self.base_url = "https://www.thestar.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _get_latest_news(self) -> List[Post]:
        """
        Scrapes the latest news from the Toronto Star homepage.
        
        Returns:
            List[Post]: List of posts from the Toronto Star
        """
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            posts = []
            # Find all article elements
            articles = soup.find_all('article', class_='tnt-asset-type-article')
            
            for article in articles:
                try:
                    # Extract article URL and title
                    headline_elem = article.find('h3', class_='tnt-headline')
                    if not headline_elem:
                        continue
                        
                    link_elem = headline_elem.find('a')
                    if not link_elem:
                        continue
                        
                    url = link_elem.get('href')
                    if not url.startswith('http'):
                        url = self.base_url + url
                        
                    title = link_elem.get_text().strip()
                    
                    # Extract description/summary
                    desc_elem = article.find('p', class_='tnt-summary')
                    desc = desc_elem.get_text().strip() if desc_elem else ""
                    
                    # Create a post with basic information
                    post = Post(
                        url=url,
                        title=title,
                        desc=desc,
                        image_url=None,  # Will be populated later by fetch_post_full_text
                        created_at=datetime.now(),
                        source='toronto_star'
                    )
                    
                    # Fetch the full text and image URL
                    text_content, image_url = self.fetch_post_full_text(url)
                    
                    # Update the post with the image URL if available
                    if image_url:
                        post.image_url = image_url
                    
                    posts.append(post)
                    
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue
            
            return posts
            
        except Exception as e:
            print(f"Error fetching Toronto Star news: {e}")
            return []

    def fetch_post_full_text(self, url: str) -> Tuple[str, Optional[str]]:
        """
        Scrapes the full text content of a Toronto Star article.
        
        Args:
            url (str): The URL of the article to scrape
            
        Returns:
            Tuple[str, Optional[str]]: The article text and image URL if successful, None if failed
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the main content
            article_content = soup.find('div', class_='article-body')
            if not article_content:
                return None, None
            
            # Extract all paragraphs
            paragraphs = article_content.find_all('p')
            text_content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            # Extract the main image
            image_url = None
            
            # Try to find the main image
            main_image = soup.find('div', class_='article-hero-image')
            if main_image:
                img_tag = main_image.find('img')
                if img_tag:
                    image_url = img_tag.get('src')
            
            # If no main image, try to find any image in the article
            if not image_url:
                img_tag = article_content.find('img')
                if img_tag:
                    image_url = img_tag.get('src')
            
            # Ensure the URL is absolute
            if image_url and not image_url.startswith('http'):
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                else:
                    image_url = 'https://' + image_url.lstrip('/')
            
            return text_content, image_url
            
        except Exception as e:
            print(f"Error fetching article: {e}")
            return None, None 