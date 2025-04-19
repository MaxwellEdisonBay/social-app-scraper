import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dotenv import load_dotenv

from common.models.models import Post
from handlers.image_handler import ImageHandler

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("api_handler")

class APIHandler:
    """
    Handler for API interactions with the news service.
    """
    
    def __init__(self, verify_ssl=True):
        """Initialize the API handler with environment variables."""
        self.base_url = os.getenv("NEWS_SERVICE_BASE_URL", "")
        self.api_key = os.getenv("NEWS_SERVICE_API_KEY", "")
        self.author_id = os.getenv("NEWS_SERVICE_AUTHOR_ID", "")
        self.organization_id = os.getenv("NEWS_SERVICE_ORGANIZATION_ID", "")
        self.verify_ssl = verify_ssl
        self.image_handler = ImageHandler()
        
        if not self.base_url or not self.api_key or not self.author_id:
            logger.warning("NEWS_SERVICE_BASE_URL or NEWS_SERVICE_API_KEY or NEWS_SERVICE_AUTHOR_ID not set in environment variables")
        
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if not self.verify_ssl:
            logger.warning("SSL verification is disabled. This should only be used for development purposes.")
            # Suppress SSL verification warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def _map_post_to_api_format(self, post: Post) -> dict:
        """
        Maps a Post object to the API format.
        
        Args:
            post (Post): The post to map
            
        Returns:
            dict: The post in API format
        """
        # Ensure required fields are present
        if not post.url:
            raise ValueError("Post URL is required")
            
        # Extract plain text from rich text if available
        en_text_plain = None
        uk_text_plain = None
        
        if hasattr(post, 'en_text') and post.en_text:
            # If en_text contains HTML, extract plain text
            if '<' in post.en_text and '>' in post.en_text:
                # Simple HTML stripping - in production you might want to use a proper HTML parser
                en_text_plain = post.en_text.replace('<h1>', '').replace('</h1>', '\n')
                en_text_plain = en_text_plain.replace('<h2>', '').replace('</h2>', '\n')
                en_text_plain = en_text_plain.replace('<p>', '').replace('</p>', '\n')
                en_text_plain = en_text_plain.replace('<strong>', '').replace('</strong>', '')
                en_text_plain = en_text_plain.replace('<em>', '').replace('</em>', '')
                en_text_plain = en_text_plain.replace('<s>', '').replace('</s>', '')
                en_text_plain = en_text_plain.replace('<ul>', '').replace('</ul>', '\n')
                en_text_plain = en_text_plain.replace('<ol>', '').replace('</ol>', '\n')
                en_text_plain = en_text_plain.replace('<li>', '- ').replace('</li>', '\n')
                en_text_plain = en_text_plain.replace('<blockquote>', '> ').replace('</blockquote>', '\n')
                en_text_plain = en_text_plain.replace('<code>', '').replace('</code>', '')
                en_text_plain = en_text_plain.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                
                # Handle links - extract the text but not the URL
                import re
                en_text_plain = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', en_text_plain)
                
                # Remove any remaining HTML tags
                en_text_plain = re.sub(r'<[^>]+>', '', en_text_plain)
                
                # Clean up multiple newlines
                en_text_plain = re.sub(r'\n\s*\n', '\n\n', en_text_plain)
            else:
                # If no HTML, use as is
                en_text_plain = post.en_text
        
        if hasattr(post, 'uk_text') and post.uk_text:
            # If uk_text contains HTML, extract plain text
            if '<' in post.uk_text and '>' in post.uk_text:
                # Simple HTML stripping - in production you might want to use a proper HTML parser
                uk_text_plain = post.uk_text.replace('<h1>', '').replace('</h1>', '\n')
                uk_text_plain = uk_text_plain.replace('<h2>', '').replace('</h2>', '\n')
                uk_text_plain = uk_text_plain.replace('<p>', '').replace('</p>', '\n')
                uk_text_plain = uk_text_plain.replace('<strong>', '').replace('</strong>', '')
                uk_text_plain = uk_text_plain.replace('<em>', '').replace('</em>', '')
                uk_text_plain = uk_text_plain.replace('<s>', '').replace('</s>', '')
                uk_text_plain = uk_text_plain.replace('<ul>', '').replace('</ul>', '\n')
                uk_text_plain = uk_text_plain.replace('<ol>', '').replace('</ol>', '\n')
                uk_text_plain = uk_text_plain.replace('<li>', '- ').replace('</li>', '\n')
                uk_text_plain = uk_text_plain.replace('<blockquote>', '> ').replace('</blockquote>', '\n')
                uk_text_plain = uk_text_plain.replace('<code>', '').replace('</code>', '')
                uk_text_plain = uk_text_plain.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                
                # Handle links - extract the text but not the URL
                import re
                uk_text_plain = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', uk_text_plain)
                
                # Remove any remaining HTML tags
                uk_text_plain = re.sub(r'<[^>]+>', '', uk_text_plain)
                
                # Clean up multiple newlines
                uk_text_plain = re.sub(r'\n\s*\n', '\n\n', uk_text_plain)
            else:
                # If no HTML, use as is
                uk_text_plain = post.uk_text
            
        # Generate a slug from the title
        import re
        import hashlib
        from datetime import datetime
        
        # Use English title if available, otherwise use the original title
        title_to_slug = post.en_title if hasattr(post, 'en_title') and post.en_title else post.title
        
        # Convert to lowercase and replace spaces with hyphens
        slug = title_to_slug.lower()
        # Remove special characters and replace spaces with hyphens
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        # Remove multiple hyphens
        slug = re.sub(r'-+', '-', slug)
        # Trim hyphens from start and end
        slug = slug.strip('-')
        
        # Add a timestamp to ensure uniqueness
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        # Add a hash of the URL to ensure uniqueness
        url_hash = hashlib.md5(post.url.encode()).hexdigest()[:8]
        slug = f"{slug}-{timestamp}-{url_hash}"
            
        # Map the post to API format
        api_post = {
            'text': en_text_plain,  # Plain text version
            'type': 'news',
            'author': self.author_id,  # Use author_id from .env
            'authorOrg': self.organization_id,  # Use organization_id from .env
            'children': [],  # Empty array for news posts
            'richText': post.en_text if hasattr(post, 'en_text') else None,  # HTML version
            'textUk': uk_text_plain,  # Plain text version
            'richTextUk': post.uk_text if hasattr(post, 'uk_text') else None,  # HTML version
            'title': post.en_title if hasattr(post, 'en_title') else None,
            'titleUk': post.uk_title if hasattr(post, 'uk_title') else None,
            'mediaUrls': [],  # Empty array by default, will be populated after successful image upload
            'newsOriginalUrl': post.url,
            'newsSource': post.source if hasattr(post, 'source') else None,
            'slug': slug  # Add the generated slug
        }
        
        # Remove None values from optional fields
        api_post = {k: v for k, v in api_post.items() if v is not None}
        
        return api_post
    
    def add_post(self, post: Post) -> Optional[Dict[str, Any]]:
        """
        Add a post to the news service.
        
        Args:
            post (Post): The post to add
            
        Returns:
            Optional[Dict[str, Any]]: The response from the API, or None if the request failed
        """
        if not self.base_url or not self.api_key:
            logger.error("NEWS_SERVICE_BASE_URL or NEWS_SERVICE_API_KEY not set")
            return None
            
        try:
            # Validate required fields
            if not post.title or not post.url:
                logger.error(f"Skipping post due to missing required fields: {post.url}")
                logger.error(f"Missing fields: title={bool(post.title)}, url={bool(post.url)}")
                return None
                
            # Check if we have either description or english text
            if not post.desc and not post.en_text:
                logger.error(f"Skipping post due to missing both description and english text: {post.url}")
                return None
                
            # Check if translation was successful
            if not post.uk_title or not post.uk_text or not post.en_text:
                logger.error(f"Skipping post due to missing translation: {post.url}")
                logger.error(f"Missing fields: uk_title={bool(post.uk_title)}, "
                            f"uk_text={bool(post.uk_text)}, "
                            f"en_text={bool(post.en_text)}")
                return None
                
            # Log post details (truncated for readability)
            logger.info(f"Processing post: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
            
            # Upload image if available
            uploaded_image_url = None
            if post.image_url:
                logger.info(f"Uploading image for post: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
                uploaded_image_url = self.image_handler.upload_image(post.image_url)
                if uploaded_image_url:
                    logger.info(f"Image uploaded successfully")
                else:
                    logger.warning(f"Failed to upload image for post: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
            
            # Map the post to the API format
            api_post = self._map_post_to_api_format(post)
            
            # Add the uploaded image URL if available
            if uploaded_image_url:
                api_post["mediaUrls"] = [uploaded_image_url]
            
            # Log the request details for debugging
            logger.info(f"Sending post to news service: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
            
            # Send the post to the news service
            response = requests.post(
                f"{self.base_url}/en/api/news",
                params={"apiKey": self.api_key},
                headers=self.headers,
                json={"posts": [api_post]},
                verify=self.verify_ssl,
                timeout=30
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                logger.info(f"Successfully sent post to news service: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
                response_data = response.json()
                
                # Check if the response has the expected format
                if isinstance(response_data, dict) and 'message' in response_data and response_data['message'] == "Success" and 'insertedPosts' in response_data:
                    return response_data
                else:
                    logger.warning(f"Unexpected response format from news service: {response_data}")
                    return None
            else:
                logger.error(f"Failed to send post to news service: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
                logger.error(f"Status code: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}{'...' if len(response.text) > 200 else ''}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending post to news service: {e}")
            return None

    def get_news(self, endpoint: str):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return None

    def post_news(self, endpoint: str, data: dict):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error posting news: {e}")
            return None