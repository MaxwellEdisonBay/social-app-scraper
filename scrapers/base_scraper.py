import abc
import requests
from bs4 import BeautifulSoup
from typing import Optional

from scrapers.cache import ScraperCache
from common.models.models import Post

class BaseScraper:
    __metaclass__ = abc.ABCMeta

    def __init__(self, enable_caching = True):
        self.cache = ScraperCache(tag = self.__class__.__name__)
        self.enable_caching = enable_caching


    def fetch_updated_news(self) -> list[Post]:
        news = self._get_latest_news()
        if self.enable_caching:
            new_posts = self.cache.add_posts(news)
            return new_posts
        return news

    @abc.abstractmethod
    def _get_latest_news(self) -> list[Post]:
        return []

    @abc.abstractmethod
    def scrape_article(self, url: str) -> Optional[str]:
        """
        Scrapes the content of a specific news article.
        Must be implemented by child classes to handle site-specific article scraping.
        
        Args:
            url (str): The URL of the article to scrape
            
        Returns:
            Optional[str]: The article text if successful, None if failed
        """
        pass