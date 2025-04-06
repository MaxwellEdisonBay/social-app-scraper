import random
import time
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base_scraper import BaseScraper
from common.models.models import Post

class TestScraper(BaseScraper):
    """
    A test scraper that generates mock news posts with random numbers.
    Useful for testing the news queue functionality.
    """
    
    def __init__(self, db_handler=None, max_posts=100):
        """
        Initialize the test scraper.
        
        Args:
            db_handler: Database handler instance
            max_posts (int): Maximum number of posts to keep
        """
        super().__init__(db_handler, max_posts)
        self.base_url = "https://example.com/news"
        self.source_name = "test"
        
    def fetch_news_updates(self) -> List[Post]:
        """
        Generate mock news posts with random numbers.
        
        Returns:
            List[Post]: List of mock news posts
        """
        # Generate a random number of posts (between 3 and 8)
        num_posts = random.randint(3, 8)
        posts = []
        
        # Current time for post timestamps
        now = datetime.now()
        
        # List of possible categories for variety
        categories = ["Politics", "Technology", "Sports", "Entertainment", "Science", "Business"]
        
        for i in range(num_posts):
            # Generate a random ID for uniqueness
            post_id = random.randint(1, 1000)
            
            # Random category
            category = random.choice(categories)
            
            # Create a post with random data
            post = Post(
                url=f"{self.base_url}/article/{post_id}",
                title=f"Test {category} News {post_id}",
                desc=f"This is a test article about {category.lower()} with ID {post_id}. "
                     f"It contains some random content for testing purposes.",
                image_url=f"https://example.com/images/{post_id}.jpg",
                created_at=now - timedelta(minutes=random.randint(0, 60))
            )
            
            posts.append(post)
            
            # Small delay to simulate network latency
            time.sleep(0.1)
        
        return posts
    
    def _get_latest_news(self) -> List[Post]:
        """
        Implementation of the abstract method from BaseScraper.
        This method is called by fetch_news_updates in the parent class.
        
        Returns:
            List[Post]: List of mock news posts
        """
        # This is just a wrapper around fetch_news_updates
        return self.fetch_news_updates()
    
    def fetch_post_full_text(self, url: str) -> Optional[str]:
        """
        Generate mock full text for a post.
        
        Args:
            url (str): URL of the post
            
        Returns:
            Optional[str]: Mock full text of the post
        """
        # Extract post ID from URL
        try:
            post_id = url.split('/')[-1]
        except:
            post_id = "unknown"
            
        # Generate paragraphs of mock text
        paragraphs = []
        num_paragraphs = random.randint(3, 7)
        
        for i in range(num_paragraphs):
            paragraph = f"This is paragraph {i+1} of the article with ID {post_id}. "
            paragraph += "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            paragraph += "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            paragraph += f"The article ID {post_id} is used to ensure uniqueness. "
            paragraph += "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
            paragraphs.append(paragraph)
        
        return "\n\n".join(paragraphs)


if __name__ == "__main__":
    # Test the scraper
    scraper = TestScraper()
    
    print("=== TEST SCRAPER DEMONSTRATION ===")
    print("Generating mock news posts...")
    
    posts = scraper.fetch_news_updates()
    
    print(f"\nGenerated {len(posts)} mock posts:")
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. {post.title}")
        print(f"   URL: {post.url}")
        print(f"   Description: {post.desc}")
        print(f"   Created at: {post.created_at}")
    
    # Test fetching full text for the first post
    if posts:
        print("\n=== TESTING FULL TEXT FETCH ===")
        first_post = posts[0]
        print(f"Fetching full text for: {first_post.title}")
        
        full_text = scraper.fetch_post_full_text(first_post.url)
        print(f"\nFull text ({len(full_text)} characters):")
        print("-" * 50)
        print(full_text[:500] + "..." if len(full_text) > 500 else full_text)
        print("-" * 50) 