import os
import requests
import logging
from typing import Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("image_handler")

class ImageHandler:
    """
    Handler for uploading images to the service.
    """
    
    def __init__(self):
        """Initialize the image handler with environment variables."""
        self.base_url = os.getenv("NEWS_SERVICE_BASE_URL", "")
        self.api_key = os.getenv("NEWS_SERVICE_API_KEY", "")
        
        if not self.base_url or not self.api_key:
            logger.warning("NEWS_SERVICE_BASE_URL or NEWS_SERVICE_API_KEY not set in environment variables")
            
        # User agent for image downloads
        self.user_agent = "Mozilla/5.0 (compatible; NewsScraper/1.0; +https://example.com)"
    
    def upload_image(self, image_url: str) -> Optional[str]:
        """
        Upload an image from a URL to the service.
        
        Args:
            image_url (str): URL of the image to upload
            
        Returns:
            Optional[str]: URL of the uploaded image, or None if the upload failed
        """
        if not image_url:
            logger.warning("No image URL provided")
            return None
            
        try:
            # Download the image with proper User-Agent
            logger.info(f"Downloading image from {image_url}")
            response = requests.get(
                image_url,
                stream=True,
                timeout=10,
                headers={
                    'User-Agent': self.user_agent
                }
            )
            response.raise_for_status()
            
            # Get the file name from the URL
            parsed_url = urlparse(image_url)
            file_name = os.path.basename(parsed_url.path)
            if not file_name:
                file_name = "image.jpg"
                
            # Get the content type
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            # Prepare the file for upload
            files = {
                'file': (file_name, response.content, content_type)
            }
            
            # Upload the image - ensure we're using the correct protocol
            upload_url = f"{self.base_url}/en/api/files"
            if "localhost" in upload_url or "127.0.0.1" in upload_url:
                upload_url = upload_url.replace("https://", "http://")
                
            logger.info(f"Uploading image to {upload_url}")
            upload_response = requests.post(
                upload_url,
                files=files,
                params={'apiKey': self.api_key},  # Add API key as query parameter
                headers={
                    'Accept': 'application/json'
                },
                timeout=30,
                verify=False if "localhost" in upload_url or "127.0.0.1" in upload_url else True
            )
            upload_response.raise_for_status()
            
            # Get the URL of the uploaded image
            result = upload_response.json()
            if 'fileUrl' in result:
                logger.info(f"Image uploaded successfully: {result['fileUrl']}")
                return result['fileUrl']
            else:
                logger.error(f"Unexpected response format: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error uploading image: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading image: {e}")
            return None 