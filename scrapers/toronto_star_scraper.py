import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
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
                    
                    # Extract image URL
                    img_elem = article.find('img', class_='img-responsive')
                    image_url = None
                    
                    # First try to find schema.org ImageObject
                    image_object = article.find('div', {'itemtype': 'https://schema.org/ImageObject'})
                    if image_object:
                        # Try to get contentUrl from meta tag
                        content_url_meta = image_object.find('meta', {'itemprop': 'contentUrl'})
                        if content_url_meta:
                            image_url = content_url_meta.get('content')
                        
                        # If not found, try to get url from meta tag
                        if not image_url:
                            url_meta = image_object.find('meta', {'itemprop': 'url'})
                            if url_meta:
                                image_url = url_meta.get('content')
                    
                    # If schema.org method failed, try the traditional method
                    if not image_url and img_elem:
                        # Try to get the src attribute first
                        image_url = img_elem.get('src')
                        # If not found, try data-src
                        if not image_url:
                            image_url = img_elem.get('data-src')
                        # If still not found, try data-srcset
                        if not image_url and img_elem.get('data-srcset'):
                            srcset = img_elem.get('data-srcset')
                            # Get the first URL from srcset
                            if srcset:
                                image_url = srcset.split(',')[0].split(' ')[0]
                    
                    # Ensure the URL is absolute
                    if image_url and not image_url.startswith('http'):
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        else:
                            image_url = 'https://' + image_url.lstrip('/')
                    
                    # Extract timestamp
                    time_elem = article.find('time', class_='tnt-date')
                    created_at = None
                    if time_elem:
                        try:
                            created_at = datetime.fromisoformat(time_elem.get('datetime').replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            pass
                    
                    # Create Post object
                    post = Post(
                        title=title,
                        desc=desc,
                        url=url,
                        image_url=image_url,
                        created_at=created_at,
                        source='toronto_star'
                    )
                    
                    posts.append(post)
                    
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue
            
            return posts
            
        except Exception as e:
            print(f"Error fetching Toronto Star news: {e}")
            return []

    def fetch_post_full_text(self, url: str) -> Optional[str]:
        """
        Scrapes the full text content of a Toronto Star article.
        
        Args:
            url (str): The URL of the article to scrape
            
        Returns:
            Optional[str]: The article text if successful, None if failed
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            # Force UTF-8 encoding
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract image URL from schema.org metadata
            image_url = None
            image_container = soup.find('div', class_='image')
            if image_container:
                # Look for schema.org ImageObject
                image_object = image_container.find('div', {'itemtype': 'https://schema.org/ImageObject'})
                if image_object:
                    # Try to get contentUrl from meta tag
                    content_url_meta = image_object.find('meta', {'itemprop': 'contentUrl'})
                    if content_url_meta:
                        image_url = content_url_meta.get('content')
                    
                    # If not found, try to get url from meta tag
                    if not image_url:
                        url_meta = image_object.find('meta', {'itemprop': 'url'})
                        if url_meta:
                            image_url = url_meta.get('content')
                    
                    # If still not found, try to get src from img tag
                    if not image_url:
                        img_tag = image_object.find('img')
                        if img_tag:
                            image_url = img_tag.get('src')
                            
                            # If the URL is relative, make it absolute
                            if image_url and not image_url.startswith('http'):
                                if image_url.startswith('//'):
                                    image_url = 'https:' + image_url
                                else:
                                    image_url = 'https://' + image_url.lstrip('/')
            
            # First try to find the main article content container
            article_body = None
            
            # Try different possible selectors for the article body
            selectors = [
                'article.asset',  # New Toronto Star article class
                'article[itemtype="https://schema.org/NewsArticle"]',  # Schema.org article type
                'div.article-body',
                'div.article__body',
                'div.article-content',
                'div[data-component="article-body"]',
                'div[data-component="article-content"]',
                'main article',  # Main article element
                'main',
                'article'
            ]
            
            for selector in selectors:
                try:
                    if '[' in selector and '=' in selector:
                        # Handle attribute selectors
                        attr_part = selector.split('[')[1].split(']')[0]
                        if '=' in attr_part:
                            attr_name, attr_value = attr_part.split('=', 1)
                            attr_value = attr_value.strip('"')
                            article_body = soup.find(selector.split('[')[0], {attr_name: attr_value})
                    elif '.' in selector:
                        # Handle class selectors
                        tag, class_name = selector.split('.')
                        article_body = soup.find(tag, class_=class_name)
                    else:
                        # Handle tag selectors
                        if ' ' in selector:
                            # Handle nested selectors like 'main article'
                            parent_tag, child_tag = selector.split(' ')
                            parent = soup.find(parent_tag)
                            if parent:
                                article_body = parent.find(child_tag)
                        else:
                            article_body = soup.find(selector)
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
                
                if article_body:
                    break
            
            if not article_body:
                return "Article content could not be extracted."
            
            # Extract all text content
            text_content = []
            
            # First try to get paragraphs
            paragraphs = article_body.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if paragraphs:
                for p in paragraphs:
                    # Skip elements with certain classes or parent elements
                    skip_classes = [
                        'tnt-ads', 'share-container', 'caption', 'credit', 'trending', 'social-media',
                        'related-stories', 'more-stories', 'footer', 'header', 'nav'
                    ]
                    if any(cls in (p.get('class', []) + p.parent.get('class', [])) for cls in skip_classes):
                        continue
                        
                    # Skip elements inside certain containers
                    skip_parents = [
                        'aside', 'nav', 'header', 'footer', 
                        'div.trending', 'div.social-media', 
                        'div.related-stories', 'div.more-stories'
                    ]
                    if any(p.find_parent(tag.split('.')[-1] if '.' in tag else tag) for tag in skip_parents):
                        continue
                    
                    text = p.get_text().strip()
                    
                    # Skip unwanted content
                    skip_phrases = [
                        'Advertisement', 
                        'Share this article',
                        'Trending',
                        'More from The Star',
                        'AP NHL:',
                        'http://',
                        'https://',
                        'More U.S.',
                        'More News',
                        'Related Stories',
                        'RELATED:',
                        'READ MORE:',
                        'WATCH:',
                        'pic.twitter.com',
                        '#'
                    ]
                    if any(phrase in text for phrase in skip_phrases):
                        continue
                    
                    if text and len(text) > 20:  # Skip very short lines
                        # Clean up the text
                        text = text.replace('\n', ' ').replace('\r', ' ')
                        text = ' '.join(text.split())  # Normalize whitespace
                        
                        # Fix common encoding issues
                        replacements = {
                            'â€™': "'",
                            'â€œ': '"',
                            'â€': '"',
                            'â€"': '—',
                            'â€¦': '...',
                            'â€˜': "'",
                            'â€™s': "'s",
                            'Â­': '',  # Remove soft hyphens
                            'Â': ' ',  # Remove non-breaking spaces
                            'ðŸš¨': '🚨',  # Fix emoji
                        }
                        for old, new in replacements.items():
                            text = text.replace(old, new)
                        
                        text_content.append(text)
            
            # Join all text content with double newlines
            final_text = '\n\n'.join(text_content)
            
            # If we still don't have any text, return a default message
            if not final_text:
                return "Article content could not be extracted."
            
            # If we found an image URL, update the post in the database
            if image_url:
                # Find the post in the database by URL
                post = self.db_handler.get_post_by_url(url)
                if post:
                    post.image_url = image_url
                    self.db_handler.update_post(post)
                    print(f"Updated image URL for post: {post.title}")
            
            return final_text
            
        except requests.RequestException as e:
            print(f"Error fetching article: {e}")
            return "Error fetching article content."
        except Exception as e:
            print(f"Unexpected error scraping article: {e}")
            return "Error extracting article content." 