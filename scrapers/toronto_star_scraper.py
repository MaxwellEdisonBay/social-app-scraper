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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        # Initialize session for better performance and cookie handling
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get_latest_news(self) -> List[Post]:
        """
        Scrapes the latest news from the Toronto Star homepage.
        Only fetches basic post information without full text or images.
        
        Returns:
            List[Post]: List of posts from the Toronto Star with basic information
        """
        try:
            response = self.session.get(self.base_url)
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
                    
                    # Create a post with basic information only
                    post = Post(
                        url=url,
                        title=title,
                        desc=desc,
                        image_url=None,  # Will be populated later when fetch_post_full_text is called
                        created_at=datetime.now(),
                        source='toronto_star'
                    )
                    
                    posts.append(post)
                    
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue
            
            return posts
            
        except Exception as e:
            print(f"Error fetching Toronto Star news: {e}")
            return []

    def fetch_post_full_text(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Scrapes the full text content of a Toronto Star article.
        
        Args:
            url (str): The URL of the article to scrape
            
        Returns:
            Tuple[Optional[str], Optional[str]]: The article text and image URL if successful, None if failed
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            response.encoding = 'utf-8'  # Set proper encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for paywall
            paywall = soup.find('div', class_='paywall-container')
            if paywall:
                print("Paywall detected")
                return None, None
            
            # Extract the main content - try multiple selectors
            article_content = None
            for selector in ['article.asset', 'div.article-body', 'div[role="main"]']:
                article_content = soup.select_one(selector)
                if article_content:
                    print(f"Found content using selector: {selector}")
                    break
            
            if not article_content:
                print("No article content found")
                return None, None
            
            # Get the title
            title = soup.find('h1', {'property': 'name headline'})
            title_text = title.get_text().strip() if title else ""
            
            # Get all paragraphs from the article content
            paragraphs = []  # Use list to maintain order
            seen_texts = set()  # Track unique paragraphs
            
            # Add title if found
            if title_text:
                paragraphs.append(title_text)
                seen_texts.add(title_text)
            
            # Find all text content
            for p in article_content.find_all(['p', 'h2']):
                # Skip certain elements by class
                skip_classes = [
                    'tnt-ads', 'hidden', 'sr-only', 'gc-byline', 'teaser', 'tnt-byline',
                    'related-links', 'article-footer', 'article-tags', 'article-meta'
                ]
                if p.get('class') and any(cls in p.get('class') for cls in skip_classes):
                    continue
                
                # Skip elements with certain text patterns
                skip_texts = [
                    'ARTICLE CONTINUES BELOW',
                    'For Subscribers',
                    'Save',
                    'Gift this article',
                    'Read about',
                    'Read more about',
                    'Updated',
                    'min read',
                    'Error!',
                    'Sorry, there was an error',
                    'There was a problem',
                    'You may unsubscribe',
                    'Want more of the latest',
                    'Sign up for more',
                    'This site is protected by reCAPTCHA',
                    'Reach him via email',
                    'The latest polls on',
                    'From advance voting',
                    'what you should know',
                    'More from',
                    'Related:',
                    'Read more:',
                    'SHARE:'
                ]
                
                text = p.get_text().strip()
                
                # Skip if text matches any skip patterns
                if any(skip_text.lower() in text.lower() for skip_text in skip_texts):
                    continue
                    
                # Skip if text looks like a related article link (usually shorter and ends with common patterns)
                if len(text) < 100 and any(text.lower().endswith(end) for end in [
                    'election', 'party', 'here', 'more', 'coverage', 'latest'
                ]):
                    continue
                
                # Clean up the text - only normalize whitespace
                text = ' '.join(text.split())  # Normalize whitespace
                if text and text not in seen_texts:  # Avoid duplicates
                    paragraphs.append(text)
                    seen_texts.add(text)
            
            if not paragraphs:
                print("No paragraphs found")
                return None, None
            
            # Join paragraphs with single newline
            text_content = "\n".join(paragraphs)
            
            # Extract the main image
            image_url = None
            
            # Try multiple image selectors in order of preference
            image_selectors = [
                ('div.article-hero-image img', 'src'),  # Main hero image
                ('div.article__featured-image img', 'src'),  # Featured image
                ('figure.article-image img', 'src'),  # Article figure image
                ('picture source', 'srcset'),  # Responsive images
                ('img[property="image"]', 'src'),  # Schema.org tagged images
                ('meta[property="og:image"]', 'content')  # OpenGraph image
            ]
            
            for selector, attr in image_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    image_url = img_elem.get(attr)
                    if image_url:
                        # Skip SVG and icon images
                        if any(skip in image_url.lower() for skip in ['icon', 'svg', 'logo']):
                            continue
                            
                        # Handle srcset format (take the largest image)
                        if attr == 'srcset':
                            srcset = image_url.split(',')
                            # Extract URLs and their sizes, pick the largest
                            images = []
                            for src in srcset:
                                parts = src.strip().split()
                                if len(parts) >= 2:
                                    url = parts[0]
                                    # Convert size to number (remove 'w' suffix)
                                    size = int(parts[1].rstrip('w'))
                                    images.append((url, size))
                            if images:
                                # Sort by size descending and take the first URL
                                image_url = sorted(images, key=lambda x: x[1], reverse=True)[0][0]
                        break
            
            # If no image found in preferred locations, try any article image
            if not image_url:
                for img in article_content.find_all('img'):
                    src = img.get('src')
                    if src and not any(skip in src.lower() for skip in ['icon', 'svg', 'logo']):
                        image_url = src
                        break
            
            # Ensure the URL is absolute
            if image_url:
                # Remove any URL parameters
                image_url = image_url.split('?')[0]
                
                # Make URL absolute
                if not image_url.startswith('http'):
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    else:
                        image_url = 'https://' + image_url.lstrip('/')
            
            return text_content, image_url
            
        except Exception as e:
            print(f"Error fetching article: {e}")
            return None, None 