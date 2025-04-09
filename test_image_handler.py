import os
import logging
from dotenv import load_dotenv
from handlers.image_handler import ImageHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_image_handler")

# Load environment variables
load_dotenv()

def test_image_upload():
    """Test the image upload functionality."""
    # Initialize the image handler
    image_handler = ImageHandler()
    
    # Test image URLs - using publicly available images
    test_images = [
        "https://picsum.photos/200/300",  # Random image from Lorem Picsum
        "https://via.placeholder.com/300x200.jpg",  # Placeholder image
        "https://dummyimage.com/600x400/000/fff"  # Dummy image
    ]
    
    # Test uploading each image
    for i, image_url in enumerate(test_images):
        logger.info(f"Testing image upload {i+1}/{len(test_images)}: {image_url}")
        
        # Upload the image
        uploaded_url = image_handler.upload_image(image_url)
        
        # Check the result
        if uploaded_url:
            logger.info(f"Image uploaded successfully: {uploaded_url}")
        else:
            logger.error(f"Failed to upload image: {image_url}")
        
        # Add a small delay between uploads to avoid rate limiting
        import time
        time.sleep(1)

if __name__ == "__main__":
    # Check if the required environment variables are set
    if not os.getenv("NEWS_SERVICE_BASE_URL") or not os.getenv("NEWS_SERVICE_API_KEY"):
        logger.error("NEWS_SERVICE_BASE_URL or NEWS_SERVICE_API_KEY not set in environment variables")
        exit(1)
    
    # Run the test
    test_image_upload() 