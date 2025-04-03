from pathlib import Path
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
import sys
import os

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)
    
from scrapers.base_scraper import BaseScraper
from common.models.models import Post


class BBCScraper(BaseScraper):

    def _get_latest_news(self) -> List[Post]:
        """
        Crawls the BBC News US & Canada page and extracts the latest news articles.

        Returns:
            A list of dictionaries, where each dictionary represents an article
            and contains the title, link, and summary (if available).
            Returns None if an error occurs.
        """
        base_url = 'https://www.bbc.com'
        url = base_url + "/news/us-canada"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            soup = BeautifulSoup(response.content, "html.parser")

            articles = []
            article_elements = soup.find_all("div", {"data-testid": "dundee-card"},
                                             recursive=True)  # find all the promo divs that contain articles.

            for element in article_elements:
                image_el = element.find("img")
                link_el = element.find("a")
                title_el = element.find("h2")
                desc_el = element.find("p")
                if link_el.get("href") is not None and image_el.get("src") is not None:
                    articles.append(
                        Post(
                            url=base_url + link_el.get("href"),
                            title=title_el.text,
                            desc=desc_el.text,
                            image_url=base_url + image_el.get("src")
                        )
                    )
            return articles

        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    def scrape_article(self, url: str) -> Optional[str]:
        """
        Scrapes the content of a BBC news article.
        
        Args:
            url (str): The URL of the BBC article to scrape
            
        Returns:
            Optional[str]: The article text if successful, None if failed
        """
        try:
            # Get the webpage content
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Find all text blocks in the article
            text_blocks = soup.find_all("div", {"data-component": "text-block"})
            
            if not text_blocks:
                return None
                
            # Extract text from each block
            article_text = []
            for block in text_blocks:
                # Get all paragraphs in the block
                paragraphs = block.find_all("p")
                
                for p in paragraphs:
                    # Get text content, preserving links
                    text = ""
                    for element in p.stripped_strings:
                        text += element + " "
                    article_text.append(text.strip())
            
            # Join all paragraphs with newlines
            return "\n\n".join(article_text)
            
        except Exception as e:
            print(f"Error scraping BBC article {url}: {e}")
            return None


if __name__ == "__main__":
    scraper = BBCScraper(enable_caching=False)
    
    # Test scrape_article with a specific URL
    test_url = "https://www.bbc.com/news/articles/c1eg7n41xq3o"
    print("\nTesting scrape_article with URL:", test_url)
    article_content = scraper.scrape_article(test_url)
    
    if article_content:
        print("\nArticle content:")
        print("-" * 50)
        print(article_content)
        print("-" * 50)
    else:
        print("\nFailed to scrape article content")
    
    # Original tests
    # print("\nTesting fetch_updated_news:")
    # print(scraper.fetch_updated_news())
    # print(scraper.fetch_updated_news())
