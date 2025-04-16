import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional

from common.models.models import Post
from scrapers.base_scraper import BaseScraper


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
                
                # Initialize image_el as None
                image_el = None
                
                # First try to find image in the card media wrapper
                media_wrapper = element.find("div", {"data-testid": "card-media"})
                if media_wrapper:
                    print("Found card media wrapper")
                    # Look for all img tags within the media wrapper
                    for img in media_wrapper.find_all("img"):
                        # Skip placeholder images
                        if "placeholder" in img.get("src", "").lower():
                            continue
                        # Check if this img has a srcset
                        if img.get("srcset"):
                            image_el = img
                            break
                        # If no srcset but has a valid src, use this img
                        elif img.get("src") and "placeholder" not in img.get("src", "").lower():
                            image_el = img
                            break
                
                # If still no image, look for video preview
                if not image_el:
                    print("Looking for video card image...")
                    video_card = element.find("div", {"data-testid": "dundee-video"})
                    if video_card:
                        print("Found video card")
                        # Look for image in the video card's media wrapper
                        media_wrapper = video_card.find("div", {"data-testid": "card-media"})
                        if media_wrapper:
                            # Look for all img tags within the media wrapper
                            for img in media_wrapper.find_all("img"):
                                # Skip placeholder images
                                if "placeholder" in img.get("src", "").lower():
                                    continue
                                # Check if this img has a srcset
                                if img.get("srcset"):
                                    image_el = img
                                    break
                                # If no srcset but has a valid src, use this img
                                elif img.get("src") and "placeholder" not in img.get("src", "").lower():
                                    image_el = img
                                    break
                
                link_el = element.find("a")
                title_el = element.find("h2", {"data-testid": "card-headline"})
                desc_el = element.find("p", {"data-testid": "card-description"})
                
                # Check if we have a valid link and image
                if link_el and link_el.get("href") and image_el:
                    # Get the image URL
                    image_url = None
                    
                    # First try to get the highest quality image from srcset
                    srcset = image_el.get("srcset", "")
                    if srcset:
                        try:
                            print(f"Processing srcset: {srcset}")
                            # Split srcset into individual URLs and find the highest resolution
                            # Format: "url1 size1w, url2 size2w, ..."
                            srcset_parts = [part.strip().split(" ") for part in srcset.split(",")]
                            print(f"Srcset parts: {srcset_parts}")
                            # Filter out any malformed entries and extract width numbers
                            valid_parts = [(url, int(size.replace("w", ""))) 
                                         for url, size in srcset_parts 
                                         if url and size.endswith("w")]
                            print(f"Valid parts: {valid_parts}")
                            if valid_parts:
                                # Sort by width and get the URL with the highest width
                                image_url = max(valid_parts, key=lambda x: x[1])[0]
                                print(f"Selected highest quality image: {image_url}")
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing srcset: {e}")
                    
                    # If no valid srcset or couldn't parse it, fall back to src
                    if not image_url:
                        print("Falling back to src attribute")
                        image_url = image_el.get("src")
                        
                        # Skip placeholder images
                        if "placeholder" in image_url.lower():
                            print("Skipping placeholder image")
                            continue
                    
                    # If the image URL is relative, make it absolute
                    if image_url and not image_url.startswith('http'):
                        image_url = base_url + image_url
                        print(f"Made image URL absolute: {image_url}")
                    
                    print(f"Final image URL: {image_url}")
                    
                    articles.append(
                        Post(
                            url=base_url + link_el.get("href"),
                            title=title_el.text.strip() if title_el else "No title available",
                            desc=desc_el.text.strip() if desc_el else "No description available",
                            image_url=image_url,
                            created_at=datetime.now(),
                            source='bbc'
                        )
                    )
            return articles

        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []
            
        except requests.RequestException as e:
            print(f"Error fetching BBC news: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in BBC scraper: {e}")
            return []

    def fetch_post_full_text(self, url: str) -> Optional[str]:
        """
        Scrapes the full text content of a BBC news article.
        
        Args:
            url (str): The URL of the article to scrape
            
        Returns:
            Optional[str]: The article text if successful, None if failed
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find all text blocks using data-component attribute
            text_blocks = soup.find_all("div", {"data-component": "text-block"})
            if not text_blocks:
                return None
            
            # Get all paragraphs from text blocks
            text_content = []
            for block in text_blocks:
                # Find all paragraphs within the text block
                paragraphs = block.find_all("p")
                for p in paragraphs:
                    # Skip empty paragraphs or those with only whitespace
                    text = p.get_text().strip()
                    if text:
                        text_content.append(text)
            
            # Join all paragraphs with newlines
            return "\n\n".join(text_content)
            
        except requests.RequestException as e:
            print(f"Error fetching article: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping article: {e}")
            return None


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
