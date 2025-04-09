import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

from handlers.api_handler import APIHandler
from common.models.models import Post

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_api_handler")

def test_api_handler():
    """Test the API handler by sending a test post."""
    # Create a test post
    test_post = Post(
        title="Test Post",
        desc="This is a test post for the API handler",
        url="https://example.com/test-post",
        source="test",
        created_at=datetime.now(),
        image_url="https://example.com/test-image.jpg"
    )
    
    # Initialize the API handler with SSL verification disabled for development
    api_handler = APIHandler(verify_ssl=False)
    
    # Check if the API handler is configured correctly
    if not api_handler.base_url or not api_handler.api_key or not api_handler.author_id:
        logger.error("API handler is not configured correctly. Please set NEWS_SERVICE_BASE_URL, NEWS_SERVICE_API_KEY, and NEWS_SERVICE_AUTHOR_ID environment variables.")
        return
    
    # Send the test post
    logger.info("Sending test post to news service...")
    result = api_handler.add_post(test_post)
    
    if result:
        logger.info(f"Test post sent successfully: {json.dumps(result, indent=2)}")
    else:
        logger.error("Failed to send test post")

if __name__ == "__main__":
    test_api_handler() 