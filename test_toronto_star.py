#!/usr/bin/env python
import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import and run the tests
from scrapers.test_toronto_star_scraper import TestTorontoStarScraper

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False) 