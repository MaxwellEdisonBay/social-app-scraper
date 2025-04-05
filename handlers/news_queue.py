import os
from datetime import datetime
from typing import List, Optional

from common.models.models import Post
from handlers.db_handler import DatabaseHandler
from handlers.ml_handler import get_relevant_posts, get_article_translation

class NewsQueue:
    def __init__(self, max_posts: int = 1000, gemini_api_key: Optional[str] = None):
        """
        Initialize the news queue with database caching.
        
        Args:
            max_posts (int): Maximum number of posts to keep in the queue
            gemini_api_key (Optional[str]): Gemini API key for ML processing
        """
        self.db_handler = DatabaseHandler(db_path=os.getenv('NEWS_QUEUE_DB_PATH'), max_posts=max_posts)
        self.gemini_api_key = gemini_api_key
    
    def add_posts(self, posts: List[Post], source: str) -> List[Post]:
        """
        Add new posts to the queue, filtering for relevance and handling translations.
        
        Args:
            posts (List[Post]): List of posts to add
            source (str): Source of the posts (e.g., 'bbc', 'reuters')
            
        Returns:
            List[Post]: List of successfully added posts
        """
        if not posts:
            return []
            
        # Get existing posts for relevance checking
        existing_posts = self.db_handler.get_all_posts()
        
        # Filter for relevance if API key is provided
        if self.gemini_api_key:
            relevant_urls = get_relevant_posts(posts, self.gemini_api_key)
            posts = [post for post in posts if post.url in relevant_urls]
        
        # Process and add each post
        added_posts = []
        for post in posts:
            # Skip if post already exists
            if self.db_handler.get_post_by_url(post.url):
                continue
                
            # Process with ML if API key is provided
            if self.gemini_api_key:
                try:
                    # Get article content
                    article_content = self._get_article_content(post.url)
                    if article_content:
                        # Get translations and improvements
                        uk_title, en_text, uk_text = get_article_translation(
                            self.gemini_api_key,
                            post.title,
                            article_content
                        )
                        
                        if uk_title and en_text and uk_text:
                            post.ukrainian_title = uk_title
                            post.english_summary = en_text
                            post.ukrainian_summary = uk_text
                except Exception as e:
                    print(f"Error processing post with ML: {e}")
            
            # Add to database
            if self.db_handler.add_post(post, source):
                added_posts.append(post)
        
        return added_posts
    
    def get_posts(self, source: Optional[str] = None) -> List[Post]:
        """
        Get all posts from the queue, optionally filtered by source.
        
        Args:
            source (Optional[str]): Source to filter posts by
            
        Returns:
            List[Post]: List of posts
        """
        return self.db_handler.get_all_posts(source)
    
    def get_post(self, url: str) -> Optional[Post]:
        """
        Get a specific post by URL.
        
        Args:
            url (str): URL of the post to retrieve
            
        Returns:
            Optional[Post]: Post object if found, None otherwise
        """
        return self.db_handler.get_post_by_url(url)
    
    def update_post(self, post: Post) -> bool:
        """
        Update an existing post in the queue.
        
        Args:
            post (Post): Post object with updated information
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        return self.db_handler.update_post(post)
    
    def _get_article_content(self, url: str) -> Optional[str]:
        """
        Get the full content of an article.
        This is a placeholder method that should be implemented based on the source.
        
        Args:
            url (str): URL of the article
            
        Returns:
            Optional[str]: Article content if successful, None otherwise
        """
        # This should be implemented based on the source
        # For now, return None
        return None


if __name__ == "__main__":
    # Test the news queue
    API_KEY = os.getenv("GOOGLE_API_KEY")
    queue = NewsQueue(max_posts=100, gemini_api_key=API_KEY)
    
    # Test data
    test_posts = [
        Post(
            url="https://example.com/test1",
            title="Test Article 1",
            desc="This is a test article about Ukrainian immigration",
            image_url="https://example.com/image1.jpg",
            created_at=datetime.now()
        ),
        Post(
            url="https://example.com/test2",
            title="Test Article 2",
            desc="This is a test article about sports",
            image_url="https://example.com/image2.jpg",
            created_at=datetime.now()
        )
    ]
    
    print("Adding test posts...")
    added_posts = queue.add_posts(test_posts, "test")
    
    print(f"\nAdded {len(added_posts)} posts:")
    for post in added_posts:
        print(f"\nTitle: {post.title}")
        print(f"URL: {post.url}")
        if post.english_summary:
            print(f"English Summary: {post.english_summary}")
        if post.ukrainian_title:
            print(f"Ukrainian Title: {post.ukrainian_title}")
        if post.ukrainian_summary:
            print(f"Ukrainian Summary: {post.ukrainian_summary}")
    
    print("\nGetting all posts:")
    all_posts = queue.get_posts()
    print(f"Total posts in queue: {len(all_posts)}")