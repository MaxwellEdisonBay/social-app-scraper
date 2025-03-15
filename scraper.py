import requests
from bs4 import BeautifulSoup

class WebCrawler:
    def __init__(self, base_url):
        self.base_url = base_url

    def fetch_page(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup

    def crawl(self, path):
        # url = f"{self.base_url}{path}"
        # html_content = self.fetch_page(url)
        # if html_content:
        #     soup = self.parse_html(html_content)
        #     # Add parsing logic here
        #     return soup
        print("Do some crawling on "    + self.base_url + path)
        return None

if __name__ == "__main__":
    crawler = WebCrawler("https://example.com")
    result = crawler.crawl("/")
    if result:
        print(result.prettify())