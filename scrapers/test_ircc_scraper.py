import unittest
from scrapers.ircc_scraper import IRCCScraper
from common.models.models import Post
import requests
from bs4 import BeautifulSoup

class TestIRCCScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = IRCCScraper(enable_caching=False)
    
    def test_get_latest_news(self):
        """Test that we can fetch the latest news from IRCC"""
        posts = self.scraper.fetch_post_updates()
        self.assertIsInstance(posts, list)
        if posts:  # If we got any posts
            post = posts[0]
            self.assertIsInstance(post, Post)
            self.assertTrue(post.title)
            self.assertTrue(post.url)
            self.assertTrue(post.created_at)
            
    def test_fetch_post_full_text(self):
        """Test that we can fetch the full text of an article"""
        # Sample HTML for testing
        sample_html = """
        <div id="news-release-container">
            <div>
                <h1 property="name headline" id="wb-cont"><strong>The Government of Canada is investing more than $9.3 million to support Francophone minority communities</strong></h1>
                <p class="gc-byline"><strong>From: <a href="/en/immigration-refugees-citizenship.html">Immigration, Refugees and Citizenship Canada</a></strong></p>
            </div>
            <div>
                <h2>News release</h2>
            </div>
            <p class="teaser hidden">Francophone immigration plays a crucial role in growing the Canadian economy, in promoting the vitality of Francophone minority communities and in meeting labour needs across the country.</p>
            <div class="mrgn-bttm-md">
                <div class="row">
                    <div class="col-md-auto">
                        <div class="cmp-text">
                            <p><strong>March 20, 2025</strong>—<strong>Ottawa</strong>—Francophone immigration plays a crucial role in growing the Canadian economy.</p>
                        </div>
                    </div>
                </div>
            </div>
            <div>
                <h2>Quotes</h2>
            </div>
            <blockquote data-emptytext="Blockquote">
                <p>"On this International Francophonie Day, I am pleased to announce concrete investments for the growth of Francophone communities."</p>
                <p>– The Honourable Rachel Bendayan, Minister of Immigration, Refugees and Citizenship</p>
            </blockquote>
            <div>
                <h2>Quick facts</h2>
            </div>
            <ul>
                <li>
                    <p>The Centre for Innovation in Francophone Immigration (CIFI) has the national mandate to integrate the Francophone perspective into immigration programs.</p>
                </li>
            </ul>
            <section class="lnkbx well">
                <h2 class="mrgn-tp-0">Associated links</h2>
                <ul>
                    <li>
                        <a href="/en/immigration-refugees-citizenship/campaigns/cifi.html">Centre for Innovation in Francophone Immigration</a>
                    </li>
                </ul>
            </section>
            <div>
                <h2>Contacts</h2>
            </div>
            <p><strong>Contacts for media only</strong></p>
            <p><strong>Media Relations<br></strong>Communications Sector<strong><br></strong>Immigration, Refugees and Citizenship Canada<strong><br></strong>613-952-1650<strong><br></strong><a href="mailto:media@cic.gc.ca">media@cic.gc.ca</a></p>
        </div>
        """
        
        # Create a mock response
        class MockResponse:
            def __init__(self, text):
                self.text = text
                self.status_code = 200
                
            def raise_for_status(self):
                pass
                
        # Mock the requests.get method
        def mock_get(*args, **kwargs):
            return MockResponse(sample_html)
            
        # Save the original requests.get
        original_get = requests.get
        
        try:
            # Replace requests.get with our mock
            requests.get = mock_get
            
            # Test the scraper
            text = self.scraper.fetch_post_full_text("https://www.canada.ca/en/immigration-refugees-citizenship/news/2025/03/the-government-of-canada-is-investing-more-than-93-million-to-support-francophone-minority-communities.html")
            
            # Verify the output
            self.assertIsNotNone(text)
            self.assertIn("The Government of Canada is investing more than $9.3 million", text)
            self.assertIn("Francophone immigration plays a crucial role", text)
            self.assertIn("Quotes:", text)
            self.assertIn("Quick Facts:", text)
            self.assertIn("Associated Links:", text)
            self.assertIn("Contacts:", text)
            
        finally:
            # Restore the original requests.get
            requests.get = original_get

if __name__ == '__main__':
    unittest.main() 