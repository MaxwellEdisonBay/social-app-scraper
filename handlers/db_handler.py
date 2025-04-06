import sqlite3
from datetime import datetime, timedelta
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
                    source TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    full_text TEXT
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
                    print(f"DEBUG: Post already exists in database: {post.url}")
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
                    print(f"DEBUG: Removed oldest post to make room")
                
                # Insert new post
                try:
                    cursor.execute('''
                        INSERT INTO posts (
                            url, title, desc, image_url, 
                            english_summary, ukrainian_title, ukrainian_summary,
                            created_at, source, status, full_text
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        post.url,
                        post.title,
                        post.desc,
                        post.image_url,
                        post.english_summary,
                        post.ukrainian_title,
                        post.ukrainian_summary,
                        post.created_at or datetime.now(),
                        source,  # Store the source
                        getattr(post, 'status', 'queued'),  # Get status from post or default to 'queued'
                        getattr(post, 'full_text', None)  # Store the full text
                    ))
                    conn.commit()
                    print(f"DEBUG: Successfully added post: {post.url} (status: {getattr(post, 'status', 'queued')})")
                    return True
                except sqlite3.Error as e:
                    print(f"DEBUG: Error inserting post: {e}")
                    return False
                
        except sqlite3.Error as e:
            print(f"DEBUG: Database error: {e}")
            return False
    
    def get_all_posts(self, source: Optional[str] = None, status: Optional[str] = None, since: Optional[datetime] = None) -> List[Post]:
        """
        Get all posts from the database, optionally filtered by source, status, and date.
        
        Args:
            source (Optional[str]): Source to filter posts by
            status (Optional[str]): Status to filter posts by ('queued', 'processed', etc.)
            since (Optional[datetime]): Only return posts created after this datetime
            
        Returns:
            List[Post]: List of Post objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT url, title, desc, image_url, 
                           english_summary, ukrainian_title, ukrainian_summary,
                           created_at, source, status, full_text
                    FROM posts 
                '''
                params = []
                
                conditions = []
                if source:
                    conditions.append("source = ?")
                    params.append(source)
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                if since:
                    conditions.append("created_at >= ?")
                    params.append(since.isoformat())
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                
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
                    # Set source, status, and full text
                    post.source = row[8]
                    post.status = row[9]
                    post.full_text = row[10]
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
                           created_at, source, status
                    FROM posts 
                    WHERE url = ?
                ''', (url,))
                
                row = cursor.fetchone()
                if row:
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
                    # Store the source and status as attributes
                    post.source = row[8]
                    post.status = row[9]
                    return post
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
                        ukrainian_summary = ?, created_at = ?, status = ?,
                        full_text = ?
                    WHERE url = ?
                ''', (
                    post.title,
                    post.desc,
                    post.image_url,
                    post.english_summary,
                    post.ukrainian_title,
                    post.ukrainian_summary,
                    post.created_at or datetime.now(),
                    getattr(post, 'status', 'queued'),  # Get status attribute or default to 'queued'
                    getattr(post, 'full_text', ''),  # Get full text attribute or default to empty string
                    post.url
                ))
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
            
    def update_post_status(self, url: str, status: str) -> bool:
        """
        Update the status of a post.
        
        Args:
            url (str): URL of the post to update
            status (str): New status for the post
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE posts 
                    SET status = ?
                    WHERE url = ?
                ''', (status, url))
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def close(self):
        """Close any open database connections."""
        try:
            # Since we use context managers for connections,
            # we don't need to do anything here, but this method
            # exists for completeness and future use
            pass
        except Exception as e:
            print(f"Error closing database: {e}")

    def get_recent_posts(self, days: int = 1, source: Optional[str] = None, status: Optional[str] = None) -> List[Post]:
        """
        Get posts from the last N days, optionally filtered by source and status.
        
        Args:
            days (int): Number of days to look back
            source (Optional[str]): Source to filter posts by
            status (Optional[str]): Status to filter posts by ('queued', 'processed', etc.)
            
        Returns:
            List[Post]: List of Post objects from the last N days
        """
        since = datetime.now() - timedelta(days=days)
        return self.get_all_posts(source=source, status=status, since=since)
        
    def get_post_source(self, url: str) -> Optional[str]:
        """
        Get the source of a post by its URL.
        
        Args:
            url (str): URL of the post
            
        Returns:
            Optional[str]: Source of the post if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT source FROM posts WHERE url = ?', (url,))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                return None
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        
    def wipe_database(self) -> bool:
        """
        Clear all entries from the database for testing purposes.
        This method deletes all records but keeps the table structure intact.
        
        Returns:
            bool: True if the database was successfully wiped, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM posts')
                conn.commit()
                print(f"DEBUG: Successfully wiped all entries from database: {self.db_path}")
                return True
        except sqlite3.Error as e:
            print(f"DEBUG: Error wiping database: {e}")
            return False 