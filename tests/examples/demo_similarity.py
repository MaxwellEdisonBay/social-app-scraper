#!/usr/bin/env python3
"""
Demonstration of the semantic similarity filtering functionality in NewsQueue.
This script shows how the NewsQueue filters similar posts in practice.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from handlers.news_queue import NewsQueue
from handlers.db_handler import DatabaseHandler
from tests.fixtures import (
    create_test_posts,
    create_similar_posts,
    create_dissimilar_posts,
    create_old_and_recent_posts
)

def demonstrate_similarity_filtering():
    """Demonstrate how the semantic similarity filtering works"""
    print("\n=== DEMONSTRATING SEMANTIC SIMILARITY FILTERING ===")
    
    # Get the database path from environment
    db_path = os.getenv('NEWS_QUEUE_DB_PATH', 'demo_news_queue.db')
    
    # Set up a clean database
    db_handler = DatabaseHandler(db_path=db_path)
    db_handler.wipe_database()
    db_handler.close()
    
    # Create a NewsQueue instance
    queue = NewsQueue()
    
    try:
        # Get test posts
        test_posts = create_test_posts()[:2]  # Only use first two test posts
        similar_posts = create_similar_posts()
        dissimilar_posts = create_dissimilar_posts()
        
        # Add initial posts to the backlog
        print("\n1. Adding initial posts to the backlog:")
        for post in test_posts:
            post.status = 'processed'
            queue.db_handler.add_post(post, "test")
            print(f"  - Added: {post.title}")
        
        # Add new posts to the queue
        print("\n2. Adding new posts to the queue (including similar and dissimilar ones):")
        all_new_posts = similar_posts + dissimilar_posts
        for post in all_new_posts:
            print(f"  - Attempting to add: {post.title}")
        
        # Add posts to the queue
        added_posts = queue.add_news(all_new_posts, "test")
        
        # Show which posts were added
        print("\n3. Posts that were actually added to the queue:")
        for post in added_posts:
            print(f"  - Added: {post.title}")
        
        # Show which posts were filtered out
        filtered_posts = [post for post in all_new_posts if post.url not in [p.url for p in added_posts]]
        print("\n4. Posts that were filtered out due to similarity:")
        for post in filtered_posts:
            print(f"  - Filtered: {post.title}")
        
        # Demonstrate time-based filtering
        print("\n5. Demonstrating that only recent posts are considered for similarity:")
        old_post, recent_post, new_post = create_old_and_recent_posts()
        
        # Add old and recent posts
        queue.db_handler.add_post(old_post, "test")
        print(f"  - Added old post to backlog: {old_post.title}")
        
        # Add the new post
        added_posts = queue.add_news([new_post], "test")
        print(f"  - Attempting to add: {new_post.title}")
        
        if added_posts:
            print(f"  - Result: Added (because it's only checked against recent posts)")
        else:
            print(f"  - Result: Filtered out (unexpected)")
        
        print("\n=== DEMONSTRATION COMPLETE ===")
        
    finally:
        # Clean up
        if queue:
            queue.db_handler.close()

if __name__ == "__main__":
    demonstrate_similarity_filtering() 