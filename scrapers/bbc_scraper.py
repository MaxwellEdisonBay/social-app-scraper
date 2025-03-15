import requests
from bs4 import BeautifulSoup

from scrapers.cache import ScraperCache
from scrapers.models import Post


class BBCScraper:
    def __init__(self, enable_caching = True):
        self.cache = ScraperCache()
        self.enable_caching = enable_caching

    def fetch_updated_news(self) -> list[Post]:
        news = self._get_bbc_us_canada_news()
        if self.enable_caching:
            new_posts = self.cache.add_posts(news)
            return new_posts
        return news

    def _get_bbc_us_canada_news(self) ->  list[Post] | None:
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
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None


if __name__ == "__main__":

    scraper = BBCScraper()
    print(scraper.fetch_updated_news())
    print(scraper.fetch_updated_news())
