import os
import unittest
import time
from handlers.db_handler import DatabaseHandler

class BaseTest(unittest.TestCase):
    """Base test class with common setup and teardown logic"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment for the whole test class"""
        # Use the environment variable for the database path
        cls.test_db_path = os.getenv('NEWS_QUEUE_DB_PATH', 'news_queue.db')
        
        # Set the environment variable for the database path
        os.environ['NEWS_QUEUE_DB_PATH'] = cls.test_db_path
        
        # Wipe the test database
        db_handler = DatabaseHandler(db_path=cls.test_db_path)
        db_handler.wipe_database()
        db_handler.close()
    
    def setUp(self):
        """Set up test environment for each test"""
        # Wipe the database before each test
        db_handler = DatabaseHandler(db_path=self.test_db_path)
        db_handler.wipe_database()
        db_handler.close()
    
    def tearDown(self):
        """Clean up after each test"""
        # Wait a moment to ensure connections are closed
        time.sleep(0.5)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in the class"""
        try:
            if os.path.exists(cls.test_db_path):
                os.remove(cls.test_db_path)
        except PermissionError:
            print(f"Warning: Could not remove test database file: {cls.test_db_path}") 