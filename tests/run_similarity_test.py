#!/usr/bin/env python3
"""
Run the semantic similarity tests for the NewsQueue class.
This script demonstrates how the NewsQueue filters similar posts.
"""

import os
import sys
import unittest
import time
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models.models import Post
from handlers.news_queue import NewsQueue
from tests.test_news_queue_similarity import TestNewsQueueSimilarity
from handlers.db_handler import DatabaseHandler

# Use the same environment variable for database path
DEMO_DB_PATH = os.getenv('NEWS_QUEUE_DB_PATH', 'news_queue.db')

def run_tests():
    """Run the unit tests"""
    print("Running semantic similarity tests...")
    unittest.main(argv=[''], verbosity=2, exit=False)

def demonstrate_functionality():
    """Demonstrate the semantic similarity filtering functionality"""
    print("\n=== DEMONSTRATING SEMANTIC SIMILARITY FILTERING ===")
    
    # Use the environment variable for the database path
    test_db_path = DEMO_DB_PATH
    
    # Set the environment variable for the database path
    os.environ['NEWS_QUEUE_DB_PATH'] = test_db_path
    
    # Wipe the database instead of trying to delete the file
    db_handler = DatabaseHandler(db_path=test_db_path)
    db_handler.wipe_database()
    db_handler.close()
    
    # Create a NewsQueue instance
    queue = NewsQueue()
    
    try:
        # Create some test posts
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
        
        # Add these posts to the backlog (as if they were already processed)
        print("\n1. Adding initial posts to the backlog:")
        for post in test_posts:
            post.status = 'processed'
            queue.db_handler.add_post(post, "test")
            print(f"  - Added: {post.title}")
        
        # Create some similar posts
        similar_posts = [
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
        
        # Create some dissimilar posts
        dissimilar_posts = [
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
        
        # Add new posts to the queue
        print("\n2. Adding new posts to the queue (including similar and dissimilar ones):")
        all_new_posts = similar_posts + dissimilar_posts
        for post in all_new_posts:
            print(f"  - Attempting to add: {post.title}")
        
        # Add posts to the queue
        added_posts = queue.add_news(all_new_posts, "test")
        
        # Check which posts were added
        print("\n3. Posts that were actually added to the queue:")
        for post in added_posts:
            print(f"  - Added: {post.title}")
        
        # Check which posts were filtered out
        filtered_posts = [post for post in all_new_posts if post.url not in [p.url for p in added_posts]]
        print("\n4. Posts that were filtered out due to similarity:")
        for post in filtered_posts:
            print(f"  - Filtered: {post.title}")
        
        # Demonstrate that only recent posts are considered for similarity
        print("\n5. Demonstrating that only recent posts are considered for similarity:")
        
        # Add an old post to the backlog (more than 1 day ago)
        old_post = Post(
            url="https://example.com/old",
            title="Old Article",
            desc="This is an old article",
            image_url="https://example.com/old.jpg",
            created_at=datetime.now() - timedelta(days=2),
            status='processed'
        )
        queue.db_handler.add_post(old_post, "test")
        print(f"  - Added old post to backlog: {old_post.title}")
        
        # Create a new post similar to the old one
        new_post = Post(
            url="https://example.com/new",
            title="New Article",
            desc="This is a new article similar to the old one",
            image_url="https://example.com/new.jpg",
            created_at=datetime.now()
        )
        
        # Add the new post to the queue
        added_posts = queue.add_news([new_post], "test")
        print(f"  - Attempting to add: {new_post.title}")
        
        # The new post should be added because it's only checked against recent posts
        if added_posts:
            print(f"  - Result: Added (because it's only checked against recent posts)")
        else:
            print(f"  - Result: Filtered out (unexpected)")
        
        print("\n=== DEMONSTRATION COMPLETE ===")
        
    finally:
        # Clean up
        if queue:
            queue.db_handler.close()
            
            # Wait a moment to ensure the connection is fully closed
            time.sleep(0.5)
            
            # Try to remove the database file
            try:
                if os.path.exists(test_db_path):
                    os.remove(test_db_path)
            except PermissionError:
                # If we can't remove the file, just log it and continue
                print(f"Warning: Could not remove demo database file: {test_db_path}")
                # Try to force close any remaining connections
                queue = None

def main():
    """Run the demonstration of semantic similarity filtering."""
    # Use the environment variable for the database path
    test_db_path = DEMO_DB_PATH
    
    # Set the environment variable for the database path
    os.environ['NEWS_QUEUE_DB_PATH'] = test_db_path
    
    # Wipe the demo database instead of trying to delete the file
    db_handler = DatabaseHandler(db_path=test_db_path)
    db_handler.wipe_database()
    db_handler.close()
    
    # Create a news queue with the demo database
    queue = NewsQueue()

if __name__ == "__main__":
    # Run the unit tests
    run_tests()
    
    # Demonstrate the functionality
    demonstrate_functionality() 