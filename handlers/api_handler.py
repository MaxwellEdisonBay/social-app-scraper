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
    
    def _map_post_to_api_format(self, post: Post) -> Dict[str, Any]:
        """
        Map a Post object to the API format.
        
        Args:
            post (Post): The post to map
            
        Returns:
            Dict[str, Any]: The mapped post data
        """
        # Map the post to the API format
        api_post = {
            "text": post.desc or "",  # Use description as text
            "type": "news",  # Assuming news is a valid PostTypes value
            "author": self.author_id,  # Default author
            "children": [],  # No children posts
            "title": post.title,
            "titleUk": post.uk_title if hasattr(post, 'uk_title') else None,
            "textUk": post.uk_text if hasattr(post, 'uk_text') else None,
            "richText": post.en_text if hasattr(post, 'en_text') else None,
            "richTextUk": post.uk_text if hasattr(post, 'uk_text') else None,
            "mediaUrls": [],  # Will be populated after image upload
            "newsOriginalUrl": post.url,  # Add the original URL of the news article
            "newsSource": post.source.upper() if post.source else None,  # Add the source of the news article
        }
        
        # Remove None values
        return {k: v for k, v in api_post.items() if v is not None}
    
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
            # Upload image if available
            uploaded_image_url = None
            if post.image_url:
                logger.info(f"Uploading image for post: {post.title}")
                uploaded_image_url = self.image_handler.upload_image(post.image_url)
                if uploaded_image_url:
                    logger.info(f"Image uploaded successfully: {uploaded_image_url}")
                else:
                    logger.warning(f"Failed to upload image for post: {post.title}")
            
            # Map the post to the API format
            api_post = self._map_post_to_api_format(post)
            
            # Add the uploaded image URL if available
            if uploaded_image_url:
                api_post["mediaUrls"] = [uploaded_image_url]
            
            # Send the post to the news service
            logger.info(f"Sending post to news service: {post.title}")
            response = requests.post(
                f"{self.base_url}/en/api/news",
                params={"apiKey": self.api_key},
                json=api_post,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            
            # Return the response
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding posts to news service: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error adding post to news service: {e}")
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