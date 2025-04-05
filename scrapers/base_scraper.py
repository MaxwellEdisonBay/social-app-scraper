from abc import ABC, abstractmethod
import os
from typing import List, Optional
from datetime import datetime
from handlers.db_handler import DatabaseHandler
from common.models.models import Post

class BaseScraper(ABC):
    def __init__(self, enable_caching: bool = True, max_posts: int = 1000):
        """
        Initialize the base scraper.
        
        Args:
            enable_caching (bool): Whether to enable caching of scraped posts
            max_posts (int): Maximum number of posts to keep in cache
        """
        self.enable_caching = enable_caching
        self.max_posts = max_posts
        self.db_handler = DatabaseHandler(db_path=os.getenv('DB_PATH'), max_posts=max_posts) if enable_caching else None
        self.source = self.__class__.__name__.lower().replace('scraper', '')
    
    @abstractmethod
    def _get_latest_news(self) -> List[Post]:
        """
        Abstract method to be implemented by child classes.
        Should return a list of Post objects from the news source.
        
        Returns:
            List[Post]: List of posts from the news source
        """
        pass
    
    def fetch_post_updates(self) -> List[Post]:
        """
        Fetches the latest news and returns only new posts not in cache.
        
        Returns:
            List[Post]: List of new posts not previously cached
        """
        try:
            # Get latest news from the source
            new_posts = self._get_latest_news()
            
            if not new_posts:
                return []
            
            if not self.enable_caching:
                return new_posts
            
            # Get existing posts from cache
            existing_posts = self.db_handler.get_all_posts(self.source)
            existing_urls = {post.url for post in existing_posts}
            
            # Filter out posts that are already in cache
            new_posts = [post for post in new_posts if post.url not in existing_urls]
            
            # Add new posts to cache
            for post in new_posts:
                self.db_handler.add_post(post, self.source)
            
            return new_posts
            
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    @abstractmethod
    def fetch_post_full_text(self, url: str) -> Optional[str]:
        """
        Scrapes the full text content of a specific news article.
        Must be implemented by child classes to handle site-specific article scraping.
        
        Args:
            url (str): The URL of the article to scrape
            
        Returns:
            Optional[str]: The article text if successful, None if failed
        """
        pass