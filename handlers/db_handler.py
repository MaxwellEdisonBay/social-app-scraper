import sqlite3
from datetime import datetime
from typing import List, Optional

from common.models.models import Post

class DatabaseHandler:
    def __init__(self, db_path: str = "news_cache.db", max_posts: int = 1000):
        """
        Initialize database handler.
        
        Args:
            db_path (str): Path to SQLite database file
            max_posts (int): Maximum number of posts to keep in the database
        """
        self.db_path = db_path
        self.max_posts = max_posts
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    desc TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    english_summary TEXT,
                    ukrainian_title TEXT,
                    ukrainian_summary TEXT,
                    created_at TIMESTAMP NOT NULL,
                    source TEXT NOT NULL
                )
            ''')
            conn.commit()
    
    def add_post(self, post: Post, source: str) -> bool:
        """
        Add a new post to the database.
        If the database is full, removes the oldest post.
        
        Args:
            post (Post): Post object to add
            source (str): Source of the post (e.g., 'bbc', 'reuters')
            
        Returns:
            bool: True if post was added, False if it already exists
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if post already exists
                cursor.execute('SELECT id FROM posts WHERE url = ?', (post.url,))
                if cursor.fetchone():
                    return False
                
                # Check if we need to remove old posts
                cursor.execute('SELECT COUNT(*) FROM posts')
                count = cursor.fetchone()[0]
                
                if count >= self.max_posts:
                    # Remove oldest post
                    cursor.execute('''
                        DELETE FROM posts 
                        WHERE id = (
                            SELECT id FROM posts 
                            ORDER BY created_at ASC 
                            LIMIT 1
                        )
                    ''')
                
                # Insert new post
                cursor.execute('''
                    INSERT INTO posts (
                        url, title, desc, image_url, 
                        english_summary, ukrainian_title, ukrainian_summary,
                        created_at, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post.url,
                    post.title,
                    post.desc,
                    post.image_url,
                    post.english_summary,
                    post.ukrainian_title,
                    post.ukrainian_summary,
                    post.created_at or datetime.now(),
                    source
                ))
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    def get_all_posts(self, source: Optional[str] = None) -> List[Post]:
        """
        Get all posts from the database, optionally filtered by source.
        
        Args:
            source (Optional[str]): Source to filter posts by
            
        Returns:
            List[Post]: List of Post objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if source:
                    cursor.execute('''
                        SELECT url, title, desc, image_url, 
                               english_summary, ukrainian_title, ukrainian_summary,
                               created_at, source
                        FROM posts 
                        WHERE source = ?
                        ORDER BY created_at DESC
                    ''', (source,))
                else:
                    cursor.execute('''
                        SELECT url, title, desc, image_url, 
                               english_summary, ukrainian_title, ukrainian_summary,
                               created_at, source
                        FROM posts 
                        ORDER BY created_at DESC
                    ''')
                
                posts = []
                for row in cursor.fetchall():
                    post = Post(
                        url=row[0],
                        title=row[1],
                        desc=row[2],
                        image_url=row[3],
                        english_summary=row[4],
                        ukrainian_title=row[5],
                        ukrainian_summary=row[6],
                        created_at=datetime.fromisoformat(row[7])
                    )
                    posts.append(post)
                return posts
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
    
    def get_post_by_url(self, url: str) -> Optional[Post]:
        """
        Get a specific post by its URL.
        
        Args:
            url (str): URL of the post to retrieve
            
        Returns:
            Optional[Post]: Post object if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT url, title, desc, image_url, 
                           english_summary, ukrainian_title, ukrainian_summary,
                           created_at, source
                    FROM posts 
                    WHERE url = ?
                ''', (url,))
                
                row = cursor.fetchone()
                if row:
                    return Post(
                        url=row[0],
                        title=row[1],
                        desc=row[2],
                        image_url=row[3],
                        english_summary=row[4],
                        ukrainian_title=row[5],
                        ukrainian_summary=row[6],
                        created_at=datetime.fromisoformat(row[7])
                    )
                return None
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
    
    def update_post(self, post: Post) -> bool:
        """
        Update an existing post in the database.
        
        Args:
            post (Post): Post object with updated information
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE posts 
                    SET title = ?, desc = ?, image_url = ?,
                        english_summary = ?, ukrainian_title = ?, 
                        ukrainian_summary = ?, created_at = ?
                    WHERE url = ?
                ''', (
                    post.title,
                    post.desc,
                    post.image_url,
                    post.english_summary,
                    post.ukrainian_title,
                    post.ukrainian_summary,
                    post.created_at or datetime.now(),
                    post.url
                ))
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False 