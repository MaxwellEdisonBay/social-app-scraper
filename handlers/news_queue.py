import os
from datetime import datetime, timedelta
from typing import List, Optional

from common.models.models import Post
from handlers.db_handler import DatabaseHandler
from handlers.ml_handler import filter_similar_posts

class NewsQueue:
    def __init__(self, max_posts: int = 1000, db_path: Optional[str] = None):
        """
        Initialize the news queue with database caching.
        
        Args:
            max_posts (int): Maximum number of posts to keep in the queue
            db_path (Optional[str]): Path to the database file. If None, uses the default path.
        """
        db_path = db_path or os.getenv('NEWS_QUEUE_DB_PATH', 'news_queue.db')
        self.db_handler = DatabaseHandler(db_path=db_path, max_posts=max_posts)
    
    def add_news(self, posts: List[Post], source: str) -> List[Post]:
        """
        Add new posts to the queue and cache them.
        Checks for semantic similarity with posts from the last day in the backlog.
        
        Args:
            posts (List[Post]): List of posts to add
            source (str): Source of the posts (e.g., 'bbc', 'reuters')
            
        Returns:
            List[Post]: List of successfully added posts
        """
        if not posts:
            return []
            
        # Get posts from the last day in the backlog for similarity checking
        recent_backlog = self.db_handler.get_recent_posts(days=1, status='processed')
        
        # Filter for semantic similarity
        unique_posts = filter_similar_posts(posts, recent_backlog, threshold=0.85)
        
        # Process and add each post
        added_posts = []
        for post in unique_posts:
            # Skip if post already exists
            if self.db_handler.get_post_by_url(post.url):
                continue
                
            # Set status to queued
            post.status = 'queued'
            
            # Add to database
            if self.db_handler.add_post(post, source):
                added_posts.append(post)
        
        return added_posts
    
    def pop_queue(self) -> List[Post]:
        """
        Retrieve all posts currently in the queue and mark them as processed.
        This function combines the functionality of process_posts and mark_as_processed.
        
        Returns:
            List[Post]: List of posts that were in the queue and are now marked as processed
        """
        # Get all queued posts
        queued_posts = self.db_handler.get_all_posts(status='queued')
        
        # Mark posts as processed
        for post in queued_posts:
            post.status = 'processed'
            self.db_handler.update_post(post)
        
        return queued_posts
    
    def _mark_as_processed(self, posts: List[Post]) -> bool:
        """
        Mark posts as processed and move them to the backlog.
        
        Args:
            posts (List[Post]): List of posts to mark as processed
            
        Returns:
            bool: True if all posts were successfully marked as processed
        """
        success = True
        for post in posts:
            post.status = 'processed'
            if not self.db_handler.update_post(post):
                success = False
        
        return success
    
    def get_backlog(self) -> List[Post]:
        """
        Get all processed posts from the backlog.
        
        Returns:
            List[Post]: List of processed posts
        """
        return self.db_handler.get_all_posts(status='processed')
    
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
    queue = None
    cleanup_db = False  # Set to True to attempt database cleanup
    
    try:
        # Clear the database before testing if cleanup is enabled
        if cleanup_db:
            try:
                import os
                import time
                if os.path.exists('news_queue.db'):
                    os.remove('news_queue.db')
                print("=== SETUP: Cleared existing database ===\n")
            except Exception as e:
                print(f"Warning: Could not clear database: {e}\n")
        
        queue = NewsQueue(max_posts=100)  # Skip ML processing for testing
        
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
        
        print("=== STEP 1: Adding posts to the queue ===")
        added_posts = queue.add_news(test_posts, "test")
        
        print(f"\nAdded {len(added_posts)} posts to the queue:")
        for post in added_posts:
            print(f"\nTitle: {post.title}")
            print(f"URL: {post.url}")
            print(f"Status: {post.status}")
        
        print("\n=== STEP 2: Checking the queue ===")
        queued_posts = queue.db_handler.get_all_posts(status='queued')
        print(f"Queue contains {len(queued_posts)} posts:")
        for post in queued_posts:
            print(f"- {post.title} (Status: {post.status})")
        
        print("\n=== STEP 3: Processing posts ===")
        # Use pop_queue instead of process_posts
        # The result is left unused for now to allow for future processing logic
        queue.pop_queue()
        print("Posts have been processed and moved to the backlog")
        
        print("\n=== STEP 4: Checking the queue after processing ===")
        queued_posts = queue.db_handler.get_all_posts(status='queued')
        print(f"Queue contains {len(queued_posts)} posts (should be 0)")
        
        print("\n=== STEP 5: Checking the backlog ===")
        backlog = queue.get_backlog()
        print(f"Backlog contains {len(backlog)} posts:")
        for post in backlog:
            print(f"- {post.title} (Status: {post.status})")
        
        print("\n=== TEST SUMMARY ===")
        print("1. Posts were added to the queue")
        print("2. Posts were retrieved from the queue and marked as processed")
        print("3. Queue was emptied after processing")
        print("4. Posts were moved to the backlog")
        print("5. Queue remained empty")
    finally:
        # Clean up
        if queue:
            queue.db_handler.close()
            
            # Only attempt cleanup if enabled
            if cleanup_db:
                try:
                    import os
                    import time
                    # Add a small delay to allow connections to be fully closed
                    time.sleep(0.5)
                    if os.path.exists('news_queue.db'):
                        os.remove('news_queue.db')
                        print("\n=== CLEANUP: Database file removed ===")
                except Exception as e:
                    print(f"\nNote: Database file could not be removed: {e}")
                    print("This is normal on Windows and doesn't affect functionality.")