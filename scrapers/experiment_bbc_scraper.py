import asyncio
from typing import List, Optional, Tuple
from pyppeteer import launch
from pyppeteer.errors import BrowserError, TimeoutError as PyppeteerTimeoutError
from bs4 import BeautifulSoup

from common.models.models import Post
from scrapers.base_scraper import BaseScraper
import os
import requests

class ExperimentBBCScraper(BaseScraper):
    def __init__(self, enable_caching: bool = True):
        super().__init__(enable_caching=enable_caching)
        self.headers = {  # These headers are less critical with a full browser
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "TE": "Trailers",
            "Cache-Control": "max-age=0",
        }

    async def fetch_post_full_text(self, url: str) -> Tuple[str, Optional[str]]:
        browser = None
        try:
            browser = await launch()  # Let pyppeteer download the latest stable
            page = await browser.newPage()
            print("Page created")
            await page.goto(url)
            print("Page loaded")
            # Wait for the dynamic content to load. Adjust the timeout and selector as needed.
            await page.waitForSelector('div[data-component="image-block"]', timeout=100)
            print("Image block found")

            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            is_video = "videos" in url

            # Find all text blocks using data-component attribute
            text_blocks = soup.find_all("div", {"data-component": "text-block"})
            if not text_blocks:
                return None, None

            # Get all paragraphs from text blocks
            text_content = []
            for block in text_blocks:
                paragraphs = block.find_all("p")
                for paragraph in paragraphs:
                    text_content.append(paragraph.text.strip())

            text_content = "\n".join(text_content)

            image_block = soup.find("div", {"data-testid": "hero-image"})
            if not image_block:
                return text_content, None

            img_tag = image_block.find("img")
            if img_tag and img_tag.get("srcset"):
                src_set = img_tag.get("srcset")
                image_url = src_set.split(",")[-1].split(" ")[0]
                return text_content, image_url
            else:
                return text_content, None

        except PyppeteerTimeoutError:
            print(f"Timeout while waiting for content on {url}")
            return None, None
        except BrowserError as e:
            print(f"Error launching or using the browser: {e}")
            return None, None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None, None
        finally:
            if browser:
                await browser.close()

    def _get_latest_news(self) -> List[Post]:
        # This would also need to be adapted for pyppeteer if the content is dynamic
        # Example (conceptual - adjust selectors as needed):
        # async def get_latest(self):
        #     browser = await launch()
        #     page = await browser.newPage()
        #     await page.goto("https://www.bbc.com/news")
        #     await page.waitForSelector(".media-list__item", timeout=10000)
        #     content = await page.content()
        #     soup = BeautifulSoup(content, "html.parser")
        #     latest_news_items = soup.select(".media-list__item")
        #     posts = []
        #     for item in latest_news_items:
        #         # ... (parsing logic)
        #     await browser.close()
        #     return posts
        # return asyncio.run(get_latest(self))
        return super()._get_latest_news()