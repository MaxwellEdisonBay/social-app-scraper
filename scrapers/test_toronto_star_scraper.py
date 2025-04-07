import unittest
from datetime import datetime
from scrapers.toronto_star_scraper import TorontoStarScraper

class TestTorontoStarScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = TorontoStarScraper(enable_caching=False)

    def test_get_latest_news(self):
        posts = self.scraper._get_latest_news()
        
        # Verify we got some posts
        self.assertIsInstance(posts, list)
        self.assertGreater(len(posts), 0)
        
        # Verify post structure
        for post in posts:
            self.assertIsInstance(post.title, str)
            self.assertIsInstance(post.desc, str)
            self.assertIsInstance(post.url, str)
            self.assertTrue(post.url.startswith('https://www.thestar.com'))
            
            # Image URL is optional
            if post.image_url:
                self.assertIsInstance(post.image_url, str)
                self.assertTrue(post.image_url.startswith('http'))
            
            # Created at is optional
            if post.created_at:
                self.assertIsInstance(post.created_at, datetime)
            
            self.assertEqual(post.source, 'toronto_star')

    def test_fetch_post_full_text(self):
        # Get a post URL first
        posts = self.scraper._get_latest_news()
        self.assertGreater(len(posts), 0)
        
        # Test full text extraction
        url = posts[0].url
        full_text = self.scraper.fetch_post_full_text(url)
        
        # Verify we got some text
        self.assertIsInstance(full_text, str)
        self.assertGreater(len(full_text), 0)

if __name__ == '__main__':
    unittest.main() 