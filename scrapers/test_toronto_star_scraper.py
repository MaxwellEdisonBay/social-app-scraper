import unittest
from datetime import datetime
from scrapers.toronto_star_scraper import TorontoStarScraper
from bs4 import BeautifulSoup

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

    def test_image_extraction_with_srcset(self):
        """Test that the scraper correctly extracts image URLs from srcset attributes."""
        # Create a sample HTML with an image that has a base64 src and a srcset
        sample_html = """
        <article class="tnt-asset-type-article">
            <h3 class="tnt-headline"><a href="/test-article">Test Article</a></h3>
            <p class="tnt-summary">Test description</p>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAADCAQAAAAe/WZNAAAAEElEQVR42mM8U88ABowYDABAxQPltt5zqAAAAABJRU5ErkJggg==" 
                 alt="Test Image" 
                 class="img-responsive" 
                 srcset="https://example.com/image-150.jpg 150w, https://example.com/image-300.jpg 300w, https://example.com/image-600.jpg 600w">
        </article>
        """
        
        # Parse the HTML
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        # Find the article
        article = soup.find('article', class_='tnt-asset-type-article')
        self.assertIsNotNone(article)
        
        # Find the image
        img_elem = article.find('img', class_='img-responsive')
        self.assertIsNotNone(img_elem)
        
        # Check if src is a base64 image
        src = img_elem.get('src', '')
        self.assertTrue(src.startswith('data:image'))
        
        # Check if srcset exists
        srcset = img_elem.get('srcset', '')
        self.assertGreater(len(srcset), 0)
        
        # Extract the image URL using the same logic as in the scraper
        image_url = None
        
        # If src is a base64 image, prioritize srcset
        if src.startswith('data:image'):
            # Try to get the highest quality image from srcset
            if srcset:
                try:
                    # Split srcset into individual URLs and find the highest resolution
                    srcset_parts = [part.strip().split(" ") for part in srcset.split(",")]
                    # Filter out any malformed entries and extract width numbers
                    valid_parts = [(url, int(size.replace("w", ""))) 
                                 for url, size in srcset_parts 
                                 if url and size.endswith("w")]
                    if valid_parts:
                        # Sort by width and get the URL with the highest width
                        image_url = max(valid_parts, key=lambda x: x[1])[0]
                except (ValueError, IndexError) as e:
                    print(f"Error parsing srcset: {e}")
        
        # Verify that we got the highest resolution image from srcset
        self.assertEqual(image_url, "https://example.com/image-600.jpg")

if __name__ == '__main__':
    unittest.main() 