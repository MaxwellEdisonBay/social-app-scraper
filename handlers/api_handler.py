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
            
        # Map the post to API format
        api_post = {
            'text': post.en_text if hasattr(post, 'en_text') else None,
            'type': 'news',
            'author': self.author_id,  # Use author_id from .env
            'children': [],  # Empty array for news posts
            'richText': post.en_text if hasattr(post, 'en_text') else None,
            'textUk': post.uk_text if hasattr(post, 'uk_text') else None,
            'richTextUk': post.uk_text if hasattr(post, 'uk_text') else None,
            'title': post.en_title if hasattr(post, 'en_title') else None,
            'titleUk': post.uk_title if hasattr(post, 'uk_title') else None,
            'mediaUrls': [post.image_url] if post.image_url else [],
            'newsOriginalUrl': post.url,
            'newsSource': post.source if hasattr(post, 'source') else None
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
            logger.info(f"URL: {post.url}")
            
            # Log description or english text (whichever is available)
            if post.desc:
                logger.info(f"Description: {post.desc[:100]}{'...' if len(post.desc) > 100 else ''}")
            else:
                logger.info(f"Using English text as description: {post.en_text[:100]}{'...' if len(post.en_text) > 100 else ''}")
            
            # Upload image if available
            uploaded_image_url = None
            if post.image_url:
                logger.info(f"Uploading image for post: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
                uploaded_image_url = self.image_handler.upload_image(post.image_url)
                if uploaded_image_url:
                    logger.info(f"Image uploaded successfully: {uploaded_image_url}")
                else:
                    logger.warning(f"Failed to upload image for post: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
            
            # Map the post to the API format
            api_post = self._map_post_to_api_format(post)
            
            # Add the uploaded image URL if available
            if uploaded_image_url:
                api_post["mediaUrls"] = [uploaded_image_url]
            
            # Log the request details for debugging
            logger.info(f"DEBUG - Request details for post: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
            logger.info(f"DEBUG - API URL: {self.base_url}/en/api/news")
            logger.info(f"DEBUG - API Key: {self.api_key[:5]}... (truncated)")
            logger.info(f"DEBUG - Author ID: {self.author_id}")
            logger.info(f"DEBUG - Request payload: {json.dumps(api_post, indent=2)}")
            
            # Send the post to the news service
            logger.info(f"Sending post to news service: {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
            response = requests.post(
                f"{self.base_url}/en/api/news",
                params={"apiKey": self.api_key},
                json=api_post,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=30
            )
            
            # Log the response for debugging
            logger.info(f"DEBUG - Response status code: {response.status_code}")
            try:
                logger.info(f"DEBUG - Response body: {json.dumps(response.json(), indent=2)}")
            except:
                logger.info(f"DEBUG - Response body: {response.text}")
                
            response.raise_for_status()
            
            # Return the response
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending post to news service: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in add_post: {e}")
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