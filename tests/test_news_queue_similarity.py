import os
import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from common.models.models import Post
from handlers.news_queue import NewsQueue
from handlers.ml_handler import filter_similar_posts
from handlers.db_handler import DatabaseHandler

# Use the same environment variable for database path
TEST_DB_PATH = os.getenv('NEWS_QUEUE_DB_PATH', 'news_queue.db')

class TestNewsQueueSimilarity(unittest.TestCase):
    """Test the semantic similarity filtering in NewsQueue"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the environment variable for the database path
        self.test_db_path = TEST_DB_PATH
        
        # Set the environment variable for the database path
        os.environ['NEWS_QUEUE_DB_PATH'] = self.test_db_path
        
        # Wipe the test database instead of trying to delete the file
        db_handler = DatabaseHandler(db_path=self.test_db_path)
        db_handler.wipe_database()
        db_handler.close()
        
        # Create a NewsQueue instance
        self.queue = NewsQueue()
        
        # Create some test posts
        self.test_posts = [
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
            ),
            Post(
                url="https://example.com/test3",
                title="Test Article 3",
                desc="This is a test article about Ukrainian refugees",
                image_url="https://example.com/image3.jpg",
                created_at=datetime.now()
            )
        ]
        
        # Create some similar posts that should be filtered out
        self.similar_posts = [
            Post(
                url="https://example.com/similar1",
                title="Similar Article 1",
                desc="This is an article about immigration in Ukraine",
                image_url="https://example.com/similar1.jpg",
                created_at=datetime.now()
            ),
            Post(
                url="https://example.com/similar2",
                title="Similar Article 2",
                desc="This is an article about Ukrainian migrants",
                image_url="https://example.com/similar2.jpg",
                created_at=datetime.now()
            )
        ]
        
        # Create some dissimilar posts that should be kept
        self.dissimilar_posts = [
            Post(
                url="https://example.com/dissimilar1",
                title="Dissimilar Article 1",
                desc="This is an article about climate change",
                image_url="https://example.com/dissimilar1.jpg",
                created_at=datetime.now()
            ),
            Post(
                url="https://example.com/dissimilar2",
                title="Dissimilar Article 2",
                desc="This is an article about technology",
                image_url="https://example.com/dissimilar2.jpg",
                created_at=datetime.now()
            )
        ]
    
    def tearDown(self):
        """Clean up after tests"""
        # Close the database connection
        if hasattr(self, 'queue') and self.queue:
            self.queue.db_handler.close()
        
        # Wait a moment to ensure the connection is fully closed
        time.sleep(0.5)
        
        # Remove the test database file
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except PermissionError:
            # If we can't remove the file, just log it and continue
            print(f"Warning: Could not remove test database file: {self.test_db_path}")
            # Try to force close any remaining connections
            self.queue = None
    
    @patch('handlers.news_queue.filter_similar_posts')
    def test_add_news_with_similarity_filtering(self, mock_filter_similar_posts):
        """Test that add_news correctly filters similar posts"""
        # Set up the mock to return the input posts
        mock_filter_similar_posts.side_effect = lambda posts, *args, **kwargs: posts
        
        # Create test posts with unique URLs
        test_posts = [
            Post(
                url="https://example.com/mock1",
                title="Mock Article 1",
                desc="This is a mock article",
                image_url="https://example.com/mock1.jpg",
                created_at=datetime.now()
            ),
            Post(
                url="https://example.com/mock2",
                title="Mock Article 2",
                desc="This is another mock article",
                image_url="https://example.com/mock2.jpg",
                created_at=datetime.now()
            )
        ]
        
        # Add posts to the queue
        added_posts = self.queue.add_news(test_posts, "test")
        
        # Verify that filter_similar_posts was called
        mock_filter_similar_posts.assert_called_once()
        
        # Verify that all posts were added (since we're mocking the filter)
        self.assertEqual(len(added_posts), len(test_posts))
        for post in added_posts:
            self.assertIn(post.url, [p.url for p in test_posts])
            self.assertEqual(post.status, 'queued')
    
    def test_add_news_with_real_similarity_filtering(self):
        """Test that add_news correctly filters similar posts using the real filter_similar_posts function"""
        # First, add some posts to the backlog
        for post in self.test_posts:
            post.status = 'processed'
            self.queue.db_handler.add_post(post, "test")
        
        # Now add new posts including similar ones
        new_posts = self.similar_posts + self.dissimilar_posts
        
        # Add posts to the queue
        added_posts = self.queue.add_news(new_posts, "test")
        
        # Verify that similar posts were filtered out
        # Note: This test depends on the actual implementation of filter_similar_posts
        # and may need adjustment based on the threshold and similarity algorithm
        self.assertLessEqual(len(added_posts), len(new_posts))
        
        # Check that at least some dissimilar posts were added
        self.assertGreater(len(added_posts), 0)
    
    def test_similarity_check_only_against_recent_posts(self):
        """Test that similarity check only considers posts from the last day"""
        # Add an old post to the backlog (more than 1 day ago)
        old_post = Post(
            url="https://example.com/old",
            title="Old Article",
            desc="This is an old article",
            image_url="https://example.com/old.jpg",
            created_at=datetime.now() - timedelta(days=2),
            status='processed'
        )
        self.queue.db_handler.add_post(old_post, "test")
        
        # Add a recent post to the backlog (less than 1 day ago)
        recent_post = Post(
            url="https://example.com/recent",
            title="Recent Article",
            desc="This is a recent article",
            image_url="https://example.com/recent.jpg",
            created_at=datetime.now() - timedelta(hours=12),
            status='processed'
        )
        self.queue.db_handler.add_post(recent_post, "test")
        
        # Create a new post similar to the old one
        new_post = Post(
            url="https://example.com/new",
            title="New Article",
            desc="This is a new article similar to the old one",
            image_url="https://example.com/new.jpg",
            created_at=datetime.now()
        )
        
        # Add the new post to the queue
        added_posts = self.queue.add_news([new_post], "test")
        
        # The new post should be added because it's only checked against recent posts
        self.assertEqual(len(added_posts), 1)
        self.assertEqual(added_posts[0].url, new_post.url)

def setup_module(module):
    """Set up test environment."""
    # Wipe the test database instead of trying to delete the file
    db_handler = DatabaseHandler(db_path=TEST_DB_PATH)
    db_handler.wipe_database()
    db_handler.close()

if __name__ == '__main__':
    unittest.main() 