import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dotenv import load_dotenv

from common.models.models import Post

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
            "text": post.desc or post.english_summary,  # Use description as text
            "type": "news",  # Assuming news is a valid PostTypes value
            "author": self.author_id,  # Default author
            "children": [],  # No children posts
            "title": post.title,
            "titleUk": post.ukrainian_title,
            "textUk": post.ukrainian_summary,
            "richText": post.english_summary,
            "richTextUk": post.ukrainian_summary,
            "mediaUrls": [post.image_url] if post.image_url else [],
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
        return self.add_posts([post])
    
    def add_posts(self, posts: List[Post]) -> Optional[Dict[str, Any]]:
        """
        Add multiple posts to the news service.
        
        Args:
            posts (List[Post]): The posts to add
            
        Returns:
            Optional[Dict[str, Any]]: The response from the API, or None if the request failed
        """
        if not self.base_url or not self.api_key:
            logger.error("Cannot add posts: NEWS_SERVICE_BASE_URL or NEWS_SERVICE_API_KEY not set")
            return None
        
        try:
            # Map all posts to API format
            api_posts = [self._map_post_to_api_format(post) for post in posts]
            request_data = {"posts": api_posts}
            
            logger.info(f"Mapped post data: {json.dumps(request_data, indent=2)}")
            
            # Construct the URL - ensure we're using http:// for localhost
            base_url = self.base_url
            if "localhost" in base_url or "127.0.0.1" in base_url:
                base_url = base_url.replace("https://", "http://")
            
            url = f"{base_url}/en/api/news?apiKey={self.api_key}"
            logger.info(f"Sending request to URL: {url}")
            
            # Send the request
            logger.info(f"Sending {len(posts)} posts to news service")
            response = requests.post(
                url, 
                json=request_data,
                headers=self.headers,
                verify=self.verify_ssl
            )
            
            # Log the raw response for debugging
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            logger.info(f"Response content: {response.text[:500]}...")  # Log first 500 chars
            
            # Check the response
            if response.status_code == 200 or response.status_code == 201:
                try:
                    # Try to parse the JSON response
                    response_data = response.json()
                    logger.info(f"Successfully added {len(posts)} posts to news service")
                    return response_data
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON response: {e}")
                    logger.error(f"Raw response: {response.text}")
                    # Return a simple success message if we can't parse the JSON
                    return {"message": "Success", "raw_response": response.text}
            else:
                logger.error(f"Failed to add posts to news service: {response.status_code} - {response.text}")
                logger.error(f"Request headers: {self.headers}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding posts to news service: {e}")
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