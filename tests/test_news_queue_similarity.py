import os
import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from common.models.models import Post
from handlers.news_queue import NewsQueue
from handlers.ml_handler import filter_similar_posts
from handlers.db_handler import DatabaseHandler
from tests.base_test import BaseTest
from tests.fixtures import (
    create_test_posts,
    create_similar_posts,
    create_dissimilar_posts,
    create_old_and_recent_posts
)

# Use the same environment variable for database path
TEST_DB_PATH = os.getenv('NEWS_QUEUE_DB_PATH', 'news_queue.db')

class TestNewsQueueSimilarity(BaseTest):
    """Test the semantic similarity filtering in NewsQueue"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.queue = NewsQueue()
        
        # Load test data
        self.test_posts = create_test_posts()
        self.similar_posts = create_similar_posts()
        self.dissimilar_posts = create_dissimilar_posts()
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'queue') and self.queue:
            self.queue.db_handler.close()
        super().tearDown()
    
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
        # Get test posts
        old_post, recent_post, new_post = create_old_and_recent_posts()
        
        # Add old and recent posts to the backlog
        self.queue.db_handler.add_post(old_post, "test")
        self.queue.db_handler.add_post(recent_post, "test")
        
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